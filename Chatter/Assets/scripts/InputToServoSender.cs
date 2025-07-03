using UnityEngine;
using TMPro;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class DualInputToServoSender : MonoBehaviour
{
    public TMP_InputField inputField1;   // 输入框 1 → 控制 servo1
    public TMP_InputField inputField2;   // 输入框 2 → 控制 servo2
    public string rosTopic = "unity_angle_publisher";

    private ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<StringMsg>(rosTopic);
    }

    public void OnSendButtonClicked()
    {
        bool ok1 = float.TryParse(inputField1.text, out float angle1);
        bool ok2 = float.TryParse(inputField2.text, out float angle2);

        if (!ok1 || !ok2)
        {
            Debug.LogWarning("Invalid angle input(s)");
            return;
        }

        angle1 = Mathf.Clamp(angle1, 0f, 180f);
        angle2 = Mathf.Clamp(angle2, 0f, 180f);

        string json = $"{{\"keys\": [\"servo1\", \"servo2\"], \"values\": [{angle1:F1}, {angle2:F1}]}}";
        ros.Publish(rosTopic, new StringMsg(json));
        Debug.Log("Sent: " + json);
    }
}

