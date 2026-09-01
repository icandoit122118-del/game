using UnityEngine;

namespace VFXTestbed
{
    /// <summary>
    /// Orbit camera aimed at the effect anchor, so an effect can be judged from every
    /// angle without hand-placing the camera. Runs on unscaled time so it stays usable
    /// while the testbed is paused or in slow motion.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    [AddComponentMenu("VFX Testbed/Turntable Camera")]
    public class TurntableCamera : MonoBehaviour
    {
        [Header("Target")]
        public Transform target;

        [Header("Orbit")]
        public float yaw = 135f;
        public float pitch = 16f;
        public float orbitSpeed = 220f;
        [Tooltip("Degrees per second of automatic orbit. 0 disables it.")]
        public float autoOrbitSpeed = 0f;

        [Header("Distance")]
        public float distance = 5f;
        public float minDistance = 0.3f;
        public float maxDistance = 60f;
        public float zoomSpeed = 6f;

        [Header("Pan")]
        public float panSpeed = 1.6f;

        Vector3 _pivotOffset;

        void LateUpdate()
        {
            if (target == null) return;

            ReadInput();

            if (!Mathf.Approximately(autoOrbitSpeed, 0f))
                yaw += autoOrbitSpeed * Time.unscaledDeltaTime;

            pitch = Mathf.Clamp(pitch, -89f, 89f);
            distance = Mathf.Clamp(distance, minDistance, maxDistance);

            var rotation = Quaternion.Euler(pitch, yaw, 0f);
            var pivot = target.position + _pivotOffset;
            transform.SetPositionAndRotation(pivot - rotation * Vector3.forward * distance, rotation);
        }

        /// <summary>Recentres the orbit pivot back onto the target.</summary>
        public void ResetPivot() => _pivotOffset = Vector3.zero;

        void ReadInput()
        {
#if ENABLE_LEGACY_INPUT_MANAGER
            float dt = Time.unscaledDeltaTime;

            if (Input.GetMouseButton(1))
            {
                yaw += Input.GetAxis("Mouse X") * orbitSpeed * dt;
                pitch -= Input.GetAxis("Mouse Y") * orbitSpeed * dt;
            }

            if (Input.GetMouseButton(2))
            {
                float scale = distance * panSpeed * dt;
                _pivotOffset -= transform.right * (Input.GetAxis("Mouse X") * scale)
                              + transform.up * (Input.GetAxis("Mouse Y") * scale);
            }

            float scroll = Input.mouseScrollDelta.y;
            if (!Mathf.Approximately(scroll, 0f))
                distance *= Mathf.Exp(-scroll * zoomSpeed * 0.05f);

            if (Input.GetKeyDown(KeyCode.F)) ResetPivot();
#endif
        }
    }
}
