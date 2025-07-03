using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections.Generic;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class MultiServoSender : MonoBehaviour
{
    public Slider[] sliders;  // 拖入多个 Slider（每个控制一个舵机）
    public TextMeshProUGUI[] angleTexts;  // 显示角度的文字
    public string rosTopic = "unity_angle_publisher";  // ROS2 中的 topic 名称

    private ROSConnection ros;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<StringMsg>(rosTopic);

        for (int i = 0; i < sliders.Length; i++)
        {
            int index = i;
            sliders[i].onValueChanged.AddListener((val) => OnSliderChanged(index, val));
        }

        // 初始发送一次
        HandleAllAngles();
    }

    void OnSliderChanged(int index, float value)
    {
        if (angleTexts != null && index < angleTexts.Length)
            angleTexts[index].text = $"Servo {index + 1}: {value:F1}";

        HandleAllAngles();
    }

    void HandleAllAngles()
    {
        Dictionary<string, float> angleDict = new Dictionary<string, float>();
        for (int i = 0; i < sliders.Length; i++)
        {
            angleDict.Add($"servo{i + 1}", sliders[i].value);
        }

        string json = JsonUtility.ToJson(new Wrapper(angleDict));
        Debug.Log("Publishing JSON to ROS: " + json);

        ros.Publish(rosTopic, new StringMsg(json));
    }

    [System.Serializable]
    public class Wrapper
    {
        public List<string> keys = new List<string>();
        public List<float> values = new List<float>();

        public Wrapper(Dictionary<string, float> dict)
        {
            foreach (var kvp in dict)
            {
                keys.Add(kvp.Key);
                values.Add(kvp.Value);
            }
        }
    }
}

