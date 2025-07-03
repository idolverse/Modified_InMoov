using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Std;

public class ChatterSubscriber : MonoBehaviour
{
    void Start()
    {
        ROSConnection.GetOrCreateInstance().Subscribe<StringMsg>(
            "talk_ros",
            Callback
        );
    }

    void Callback(StringMsg msg)
    {
        Debug.Log("Received: " + msg.data);
    }
}
