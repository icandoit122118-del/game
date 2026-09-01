using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;

namespace VFXTestbed.EditorTools
{
    /// <summary>
    /// Builds a neutral stage for judging visual effects: a metric grid floor, scale
    /// references, switchable backdrops and lighting, an HDR turntable camera and an
    /// optional bloom volume. Everything is generated, so the testbed needs no
    /// downloaded art and can live in the repository without licence concerns.
    /// </summary>
    public static class VFXTestbedSceneBuilder
    {
        const string RootName = "VFX Testbed";
        const string GeneratedFolder = "Assets/VFXTestbed/Generated";
        const float FloorSizeMeters = 20f;

        [MenuItem("Tools/VFX Testbed/Build Test Stage", false, 0)]
        public static void BuildTestStage()
        {
            var existing = GameObject.Find(RootName);
            if (existing != null)
            {
                bool replace = EditorUtility.DisplayDialog(
                    "VFX Testbed",
                    $"'{RootName}' already exists in this scene. Replace it?\n\nAnything you parented under the effect anchor will be destroyed.",
                    "Replace", "Cancel");
                if (!replace) return;
                UnityEngine.Object.DestroyImmediate(existing);
            }

            EnsureGeneratedFolder();
            WarnIfGammaColorSpace();

            var root = new GameObject(RootName);
            Undo.RegisterCreatedObjectUndo(root, "Build VFX Test Stage");

            var effectAnchor = new GameObject("Effect Anchor");
            effectAnchor.transform.SetParent(root.transform, false);

            var floor = BuildFloor(root.transform, out var floorRenderer);
            var references = BuildScaleReferences(root.transform);
            var keyLight = BuildKeyLight(root.transform);
            var camera = BuildCamera(root.transform, effectAnchor.transform);
            var volume = BuildPostProcessingVolume(root.transform);

            var controller = root.AddComponent<VFXTestbedController>();
            controller.stageCamera = camera;
            controller.keyLight = keyLight;
            controller.floorRenderer = floorRenderer;
            controller.gridFloor = floor;
            controller.scaleReferences = references;
            controller.postProcessingVolume = volume;
            controller.effectAnchor = effectAnchor.transform;
            PopulatePresets(controller);

            Selection.activeGameObject = root;
            SceneView.lastActiveSceneView?.FrameSelected();

            Debug.Log("[VFX Testbed] Stage built. Parent your effect under 'VFX Testbed/Effect Anchor' and enter play mode.", root);
        }

        [MenuItem("Tools/VFX Testbed/Open VFX Graph Learning Templates docs", false, 20)]
        public static void OpenLearningTemplatesDocs() =>
            Application.OpenURL("https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.2/manual/sample-learningTemplates.html");

        // ---------------------------------------------------------------- stage parts

        static GameObject BuildFloor(Transform parent, out Renderer floorRenderer)
        {
            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "Grid Floor";
            floor.transform.SetParent(parent, false);
            // A Unity plane is 10 m across at scale 1.
            floor.transform.localScale = Vector3.one * (FloorSizeMeters / 10f);

            floorRenderer = floor.GetComponent<Renderer>();
            floorRenderer.sharedMaterial = CreateFloorMaterial();
            floorRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            return floor;
        }

        static GameObject BuildScaleReferences(Transform parent)
        {
            var group = new GameObject("Scale References");
            group.transform.SetParent(parent, false);

            var material = CreateLitMaterial("ScaleReference", new Color(0.55f, 0.55f, 0.58f));

            // 1 m cube — the unit every VFX size should be read against.
            AddReference(group.transform, PrimitiveType.Cube, "Cube 1m",
                new Vector3(2f, 0.5f, 0f), Vector3.one, material);

            // 1.8 m capsule — a stand-in for a player character.
            AddReference(group.transform, PrimitiveType.Capsule, "Human 1.8m",
                new Vector3(-2f, 0.9f, 0f), new Vector3(0.6f, 0.9f, 0.6f), material);

            // 0.5 m sphere — small-prop scale.
            AddReference(group.transform, PrimitiveType.Sphere, "Sphere 0.5m",
                new Vector3(0f, 0.25f, 2f), Vector3.one * 0.5f, material);

            return group;
        }

        static void AddReference(Transform parent, PrimitiveType type, string name,
            Vector3 position, Vector3 scale, Material material)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = material;
        }

        static Light BuildKeyLight(Transform parent)
        {
            var go = new GameObject("Key Light");
            go.transform.SetParent(parent, false);
            go.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

            var light = go.AddComponent<Light>();
            light.type = LightType.Directional;
            light.shadows = LightShadows.Soft;
            light.intensity = 1f;
            return light;
        }

        static Camera BuildCamera(Transform parent, Transform target)
        {
            var go = new GameObject("Stage Camera");
            go.transform.SetParent(parent, false);

            var camera = go.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = Color.black;
            camera.nearClipPlane = 0.05f;
            camera.farClipPlane = 200f;
            // HDR is what lets bright effects actually bloom instead of clipping to white.
            camera.allowHDR = true;
            if (Camera.main == null) camera.tag = "MainCamera";

            var turntable = go.AddComponent<TurntableCamera>();
            turntable.target = target;
            turntable.distance = 5f;
            turntable.yaw = 135f;
            turntable.pitch = 16f;

#pragma warning disable 618 // FindObjectOfType is the one spelling that exists in every supported version.
            if (UnityEngine.Object.FindObjectOfType<AudioListener>() == null)
#pragma warning restore 618
                go.AddComponent<AudioListener>();

            return camera;
        }

        static void PopulatePresets(VFXTestbedController controller)
        {
            controller.backdrops.Clear();
            controller.backdrops.Add(new VFXTestbedController.BackdropPreset
            { name = "Mid grey", color = new Color(0.21f, 0.21f, 0.22f), floorColor = new Color(0.18f, 0.18f, 0.19f) });
            controller.backdrops.Add(new VFXTestbedController.BackdropPreset
            { name = "Black", color = Color.black, floorColor = new Color(0.05f, 0.05f, 0.06f) });
            controller.backdrops.Add(new VFXTestbedController.BackdropPreset
            { name = "White", color = new Color(0.85f, 0.85f, 0.85f), floorColor = new Color(0.72f, 0.72f, 0.73f) });
            controller.backdrops.Add(new VFXTestbedController.BackdropPreset
            { name = "Dusk blue", color = new Color(0.16f, 0.20f, 0.30f), floorColor = new Color(0.13f, 0.15f, 0.20f) });

            controller.lightingPresets.Clear();
            controller.lightingPresets.Add(new VFXTestbedController.LightingPreset
            {
                name = "Studio neutral",
                ambientColor = new Color(0.26f, 0.26f, 0.29f),
                keyColor = Color.white,
                keyIntensity = 1f,
                keyRotation = new Vector3(50f, -30f, 0f),
            });
            controller.lightingPresets.Add(new VFXTestbedController.LightingPreset
            {
                // The honest test for an emissive effect: nothing lights the scene but the effect.
                name = "Black box",
                ambientColor = Color.black,
                ambientIntensity = 0f,
                keyIntensity = 0f,
            });
            controller.lightingPresets.Add(new VFXTestbedController.LightingPreset
            {
                name = "Night + fog",
                ambientColor = new Color(0.04f, 0.05f, 0.08f),
                keyColor = new Color(0.45f, 0.55f, 0.85f),
                keyIntensity = 0.25f,
                keyRotation = new Vector3(60f, -140f, 0f),
                fog = true,
                fogColor = new Color(0.03f, 0.04f, 0.06f),
                fogDensity = 0.02f,
            });
            controller.lightingPresets.Add(new VFXTestbedController.LightingPreset
            {
                name = "Daylight",
                ambientColor = new Color(0.45f, 0.50f, 0.58f),
                keyColor = new Color(1f, 0.96f, 0.89f),
                keyIntensity = 1.7f,
                keyRotation = new Vector3(55f, -20f, 0f),
            });
        }

        // ------------------------------------------------------- post processing (SRP)

        /// <summary>
        /// Creates a global volume with bloom when a scriptable render pipeline is
        /// installed. Reached through reflection so this file still compiles on a
        /// Built-in pipeline project, where no volume types exist at all.
        /// </summary>
        static GameObject BuildPostProcessingVolume(Transform parent)
        {
            var volumeType = FindType("UnityEngine.Rendering.Volume", "Unity.RenderPipelines.Core.Runtime");
            var profileType = FindType("UnityEngine.Rendering.VolumeProfile", "Unity.RenderPipelines.Core.Runtime");
            if (volumeType == null || profileType == null)
            {
                Debug.Log("[VFX Testbed] No scriptable render pipeline found — skipping the bloom volume. " +
                          "On Built-in, add your own post-processing stack and assign it to the controller's Post Processing Volume field.");
                return null;
            }

            try
            {
                var go = new GameObject("Post Processing Volume");
                go.transform.SetParent(parent, false);

                var volume = go.AddComponent(volumeType);
                volumeType.GetProperty("isGlobal")?.SetValue(volume, true);

                var profile = ScriptableObject.CreateInstance(profileType);
                var profilePath = $"{GeneratedFolder}/VFXTestbedProfile.asset";
                AssetDatabase.CreateAsset(profile, AssetDatabase.GenerateUniqueAssetPath(profilePath));

                AddBloomOverride(profileType, profile);

                AssetDatabase.SaveAssets();
                volumeType.GetProperty("sharedProfile")?.SetValue(volume, profile);
                return go;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[VFX Testbed] Could not build the bloom volume automatically ({e.Message}). " +
                                 "Add a Volume with a Bloom override by hand and assign it to the controller.");
                return null;
            }
        }

        static void AddBloomOverride(Type profileType, ScriptableObject profile)
        {
            var bloomType = FindType("UnityEngine.Rendering.Universal.Bloom", "Unity.RenderPipelines.Universal.Runtime")
                         ?? FindType("UnityEngine.Rendering.HighDefinition.Bloom", "Unity.RenderPipelines.HighDefinition.Runtime");
            if (bloomType == null) return;

            var add = profileType.GetMethod("Add", new[] { typeof(Type), typeof(bool) });
            if (add == null) return;

            var bloom = add.Invoke(profile, new object[] { bloomType, true });
            if (bloom == null) return;

            SetVolumeParameter(bloom, "threshold", 1.0f);
            SetVolumeParameter(bloom, "intensity", 0.6f);
        }

        /// <summary>Writes through a VolumeParameter's boxed <c>value</c> field.</summary>
        static void SetVolumeParameter(object component, string parameterName, float value)
        {
            var field = component.GetType().GetField(parameterName,
                BindingFlags.Public | BindingFlags.Instance);
            var parameter = field?.GetValue(component);
            if (parameter == null) return;

            parameter.GetType().GetProperty("value")?.SetValue(parameter, value);
            parameter.GetType().GetProperty("overrideState")?.SetValue(parameter, true);
        }

        static Type FindType(string typeName, string assemblyName)
        {
            var type = Type.GetType($"{typeName}, {assemblyName}");
            if (type != null) return type;

            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                type = assembly.GetType(typeName);
                if (type != null) return type;
            }
            return null;
        }

        // -------------------------------------------------------------- generated art

        static Material CreateFloorMaterial()
        {
            var material = CreateLitMaterial("GridFloor", Color.white);
            var texture = CreateGridTexture();

            foreach (var property in new[] { "_BaseMap", "_MainTex" })
            {
                if (!material.HasProperty(property)) continue;
                material.SetTexture(property, texture);
                material.SetTextureScale(property, Vector2.one * FloorSizeMeters);
            }

            if (material.HasProperty("_Smoothness")) material.SetFloat("_Smoothness", 0.05f);
            if (material.HasProperty("_Glossiness")) material.SetFloat("_Glossiness", 0.05f);
            EditorUtility.SetDirty(material);
            AssetDatabase.SaveAssets();
            return material;
        }

        static Material CreateLitMaterial(string name, Color color)
        {
            var path = $"{GeneratedFolder}/{name}.mat";
            var material = new Material(FindLitShader()) { name = name };
            foreach (var property in new[] { "_BaseColor", "_Color" })
                if (material.HasProperty(property)) material.SetColor(property, color);

            AssetDatabase.CreateAsset(material, path);
            return AssetDatabase.LoadAssetAtPath<Material>(path);
        }

        /// <summary>
        /// Picks a lit shader for whichever pipeline is installed. URP and HDRP are tried
        /// first because "Standard" still resolves inside an SRP project, where it renders
        /// magenta.
        /// </summary>
        static Shader FindLitShader()
        {
            string[] candidates =
            {
                "Universal Render Pipeline/Lit",
                "HDRP/Lit",
                "Standard",
            };

            foreach (var name in candidates)
            {
                var shader = Shader.Find(name);
                if (shader != null) return shader;
            }
            return Shader.Find("Sprites/Default");
        }

        /// <summary>
        /// One square metre of floor: a white tile with darker edges and quarter-metre
        /// subdivisions, so the material tint drives the overall value while the grid
        /// keeps a readable sense of scale.
        /// </summary>
        static Texture2D CreateGridTexture()
        {
            const int size = 256;
            const int majorLine = 3;
            const int minorStep = size / 4;

            var texture = new Texture2D(size, size, TextureFormat.RGBA32, true);
            var pixels = new Color32[size * size];

            var baseColor = new Color32(255, 255, 255, 255);
            var minorColor = new Color32(215, 215, 218, 255);
            var majorColor = new Color32(140, 140, 145, 255);

            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    bool onMajor = x < majorLine || y < majorLine
                                || x >= size - majorLine || y >= size - majorLine;
                    bool onMinor = x % minorStep == 0 || y % minorStep == 0;
                    pixels[y * size + x] = onMajor ? majorColor : onMinor ? minorColor : baseColor;
                }
            }

            texture.SetPixels32(pixels);
            texture.Apply();

            var path = $"{GeneratedFolder}/GridTexture.png";
            File.WriteAllBytes(path, texture.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(texture);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);

            if (AssetImporter.GetAtPath(path) is TextureImporter importer)
            {
                importer.wrapMode = TextureWrapMode.Repeat;
                importer.filterMode = FilterMode.Trilinear;
                importer.anisoLevel = 8;
                importer.mipmapEnabled = true;
                importer.SaveAndReimport();
            }

            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        static void EnsureGeneratedFolder()
        {
            if (AssetDatabase.IsValidFolder(GeneratedFolder)) return;
            if (!AssetDatabase.IsValidFolder("Assets/VFXTestbed"))
                AssetDatabase.CreateFolder("Assets", "VFXTestbed");
            AssetDatabase.CreateFolder("Assets/VFXTestbed", "Generated");
        }

        static void WarnIfGammaColorSpace()
        {
            if (PlayerSettings.colorSpace == ColorSpace.Linear) return;
            Debug.LogWarning("[VFX Testbed] Project colour space is Gamma. HDR effects and bloom will not " +
                             "read correctly — switch to Linear in Project Settings > Player > Other Settings.");
        }
    }
}
