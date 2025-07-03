using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class HelloPublisher : MonoBehaviour
{
    ROSConnection ros;
    string topicName = "/chatter";

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<StringMsg>(topicName);
    }

    public void SendHello()
    {
        StringMsg msg = new StringMsg("Hello from Unity");
        ros.Publish(topicName, msg);
        Debug.Log("Published: Hello from Unity");
    }
}

