using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace VFXTestbed
{
    /// <summary>
    /// Runtime driver for the VFX test stage: swaps the backdrop value, the lighting
    /// preset and the time scale so an effect can be judged the way it will actually
    /// ship — on a dark scene, on a bright one, with and without post processing.
    ///
    /// Deliberately uses only core engine types, so it compiles on Built-in, URP and
    /// HDRP alike; post processing is toggled by activating the volume GameObject
    /// rather than by touching pipeline-specific components.
    /// </summary>
    [AddComponentMenu("VFX Testbed/VFX Testbed Controller")]
    public class VFXTestbedController : MonoBehaviour
    {
        [System.Serializable]
        public class BackdropPreset
        {
            public string name = "Backdrop";
            [ColorUsage(false)] public Color color = Color.black;
            [Tooltip("Floor tint. Kept separate so the floor can stay readable on a black backdrop.")]
            [ColorUsage(false)] public Color floorColor = new Color(0.18f, 0.18f, 0.18f);
        }

        [System.Serializable]
        public class LightingPreset
        {
            public string name = "Lighting";
            public Color ambientColor = new Color(0.05f, 0.05f, 0.06f);
            [Range(0f, 8f)] public float ambientIntensity = 1f;
            public Color keyColor = Color.white;
            [Range(0f, 8f)] public float keyIntensity = 1f;
            public Vector3 keyRotation = new Vector3(50f, -30f, 0f);
            public bool fog;
            [ColorUsage(false)] public Color fogColor = Color.black;
            public float fogDensity = 0.015f;
        }

        [Header("Scene references")]
        public Camera stageCamera;
        public Light keyLight;
        public Renderer floorRenderer;
        public GameObject gridFloor;
        public GameObject scaleReferences;
        [Tooltip("Post-processing volume GameObject. Toggled with B; may be null.")]
        public GameObject postProcessingVolume;
        [Tooltip("Effects parented here are restarted by R.")]
        public Transform effectAnchor;

        [Header("Presets")]
        public List<BackdropPreset> backdrops = new List<BackdropPreset>();
        public List<LightingPreset> lightingPresets = new List<LightingPreset>();

        [Header("Time")]
        public float[] timeScales = { 1f, 0.5f, 0.25f, 0.1f };

        [Header("HUD")]
        public bool showHud = true;

        int _backdropIndex;
        int _lightingIndex;
        int _timeScaleIndex;
        bool _paused;

        static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        static readonly int ColorId = Shader.PropertyToID("_Color");
        MaterialPropertyBlock _block;

        void Start()
        {
            if (backdrops.Count == 0) backdrops.Add(new BackdropPreset());
            if (lightingPresets.Count == 0) lightingPresets.Add(new LightingPreset());
            if (timeScales == null || timeScales.Length == 0) timeScales = new[] { 1f };

            ApplyBackdrop(_backdropIndex);
            ApplyLighting(_lightingIndex);
            ApplyTimeScale();
        }

        void OnDisable()
        {
            // Never leave the editor stuck in slow motion after exiting play mode.
            Time.timeScale = 1f;
        }

        void Update() => ReadInput();

        void ReadInput()
        {
#if ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetKeyDown(KeyCode.Alpha1)) CycleBackdrop();
            if (Input.GetKeyDown(KeyCode.Alpha2)) CycleLighting();
            if (Input.GetKeyDown(KeyCode.B)) TogglePostProcessing();
            if (Input.GetKeyDown(KeyCode.G) && gridFloor != null) gridFloor.SetActive(!gridFloor.activeSelf);
            if (Input.GetKeyDown(KeyCode.C) && scaleReferences != null) scaleReferences.SetActive(!scaleReferences.activeSelf);
            if (Input.GetKeyDown(KeyCode.R)) RestartEffects();
            if (Input.GetKeyDown(KeyCode.Space)) TogglePause();
            if (Input.GetKeyDown(KeyCode.T)) CycleTimeScale();
            if (Input.GetKeyDown(KeyCode.H)) showHud = !showHud;
            if (Input.GetKeyDown(KeyCode.P)) CaptureScreenshot();
#endif
        }

        public void CycleBackdrop() => ApplyBackdrop((_backdropIndex + 1) % backdrops.Count);
        public void CycleLighting() => ApplyLighting((_lightingIndex + 1) % lightingPresets.Count);

        public void ApplyBackdrop(int index)
        {
            _backdropIndex = Mathf.Clamp(index, 0, backdrops.Count - 1);
            var preset = backdrops[_backdropIndex];

            if (stageCamera != null)
            {
                stageCamera.clearFlags = CameraClearFlags.SolidColor;
                stageCamera.backgroundColor = preset.color;
            }

            if (floorRenderer != null)
            {
                if (_block == null) _block = new MaterialPropertyBlock();
                floorRenderer.GetPropertyBlock(_block);
                // Set both names so the same block works for Standard and for SRP Lit.
                _block.SetColor(BaseColorId, preset.floorColor);
                _block.SetColor(ColorId, preset.floorColor);
                floorRenderer.SetPropertyBlock(_block);
            }
        }

        public void ApplyLighting(int index)
        {
            _lightingIndex = Mathf.Clamp(index, 0, lightingPresets.Count - 1);
            var preset = lightingPresets[_lightingIndex];

            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = preset.ambientColor;
            RenderSettings.ambientIntensity = preset.ambientIntensity;
            RenderSettings.fog = preset.fog;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = preset.fogColor;
            RenderSettings.fogDensity = preset.fogDensity;

            if (keyLight != null)
            {
                keyLight.color = preset.keyColor;
                keyLight.intensity = preset.keyIntensity;
                keyLight.transform.rotation = Quaternion.Euler(preset.keyRotation);
                keyLight.enabled = preset.keyIntensity > 0f;
            }
        }

        public void TogglePostProcessing()
        {
            if (postProcessingVolume != null)
                postProcessingVolume.SetActive(!postProcessingVolume.activeSelf);
        }

        /// <summary>
        /// Replays everything under the effect anchor. Cycling activity re-seeds VFX Graph
        /// effects and particle systems alike, which is why it is used instead of a
        /// package-specific Reinit call.
        /// </summary>
        public void RestartEffects()
        {
            if (effectAnchor == null) return;

            for (int i = 0; i < effectAnchor.childCount; i++)
            {
                var child = effectAnchor.GetChild(i).gameObject;
                if (!child.activeSelf) continue;
                child.SetActive(false);
                child.SetActive(true);
            }

            foreach (var system in effectAnchor.GetComponentsInChildren<ParticleSystem>(true))
            {
                system.Clear(true);
                system.Play(true);
            }
        }

        public void TogglePause()
        {
            _paused = !_paused;
            ApplyTimeScale();
        }

        public void CycleTimeScale()
        {
            _timeScaleIndex = (_timeScaleIndex + 1) % timeScales.Length;
            ApplyTimeScale();
        }

        void ApplyTimeScale() => Time.timeScale = _paused ? 0f : timeScales[_timeScaleIndex];

        public void CaptureScreenshot()
        {
            var path = $"VFXTestbed_{System.DateTime.Now:yyyyMMdd_HHmmss}.png";
            ScreenCapture.CaptureScreenshot(path);
            Debug.Log($"[VFX Testbed] Screenshot written to {path}");
        }

        void OnGUI()
        {
            if (!showHud) return;

            const int width = 300;
            var rect = new Rect(12f, 12f, width, 190f);
            GUI.Box(rect, "VFX Testbed");

            GUILayout.BeginArea(new Rect(rect.x + 10f, rect.y + 24f, width - 20f, rect.height - 32f));
            GUILayout.Label($"1  Backdrop : {backdrops[_backdropIndex].name}");
            GUILayout.Label($"2  Lighting : {lightingPresets[_lightingIndex].name}");
            GUILayout.Label($"B  Post FX  : {(postProcessingVolume != null && postProcessingVolume.activeSelf ? "on" : "off")}");
            GUILayout.Label($"T  Time     : {timeScales[_timeScaleIndex]:0.##}x{(_paused ? "  (paused)" : "")}");
            GUILayout.Label("R restart   Space pause   G grid");
            GUILayout.Label("C refs      H hud         P screenshot");
            GUILayout.Label("RMB orbit   MMB pan       Wheel zoom");
            GUILayout.EndArea();
        }
    }
}
