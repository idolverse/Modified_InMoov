#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include <jsoncpp/json/json.h>
#include <map>

class FaceControllerServer : public rclcpp::Node {
public:
    FaceControllerServer() : Node("face_controller_server") {
        // 初始化舵机映射
        initServoMapping();
        
        // 订阅命令话题
        command_sub_ = this->create_subscription<std_msgs::msg::String>(
            "/face_controller/command", 10,
            std::bind(&FaceControllerServer::commandCallback, this, std::placeholders::_1));
        
        // 发布响应话题
        response_pub_ = this->create_publisher<std_msgs::msg::String>(
            "/face_controller/response", 10);
        
        // 发布关节状态
        joint_state_pub_ = this->create_publisher<sensor_msgs::msg::JointState>(
            "/joint_states", 10);
    }
    
    void run() {
        rclcpp::spin(shared_from_this());
    }

private:
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr command_sub_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr response_pub_;
    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_state_pub_;
    std::map<std::string, int> servo_mapping_;
    
    void initServoMapping() {
        // 初始化舵机名称到通道的映射 (与ROS1版本相同)
        servo_mapping_["LEFT_EYE_V"] = 0;
        servo_mapping_["LEFT_EYE_H"] = 1;
        // ... 其余映射保持不变
    }
    
    void commandCallback(const std_msgs::msg::String::SharedPtr msg) {
        try {
            Json::Value root;
            Json::Reader reader;
            
            if (!reader.parse(msg->data, root)) {
                sendErrorResponse("Invalid JSON format");
                return;
            }
            
            std::string command_type = root["type"].asString();
            Json::Value data = root["data"];
            
            if (command_type == "SET_FACE_PART") {
                handleSetFacePart(data);
            } 
            else if (command_type == "SET_SERVO") {
                handleSetServo(data);
            }
            else if (command_type == "CENTER_ALL") {
                handleCenterAll();
            }
            else {
                sendErrorResponse("Unknown command type: " + command_type);
            }
        }
        catch (const std::exception& e) {
            sendErrorResponse(std::string("Error processing command: ") + e.what());
        }
    }
    
    // 其余方法与ROS1版本基本相同，只需修改消息类型和日志调用
    
    void setServoAngle(int channel, int angle) {
        // ROS2日志调用
        RCLCPP_INFO(this->get_logger(), "Setting servo %d to %d degrees", channel, angle);
        
        // 实际硬件控制代码...
    }
    
    void updateJointState(const std::string& joint_name, double position) {
        auto joint_state = sensor_msgs::msg::JointState();
        joint_state.header.stamp = this->now();
        joint_state.name.push_back(joint_name);
        joint_state.position.push_back(position * M_PI / 180.0);
        
        joint_state_pub_->publish(joint_state);
    }
    
    void sendSuccessResponse(const std::string& message) {
        Json::Value response;
        response["status"] = "success";
        response["message"] = message;
        
        auto msg = std_msgs::msg::String();
        msg.data = Json::FastWriter().write(response);
        response_pub_->publish(msg);
    }
    
    void sendErrorResponse(const std::string& message) {
        Json::Value response;
        response["status"] = "error";
        response["message"] = message;
        
        auto msg = std_msgs::msg::String();
        msg.data = Json::FastWriter().write(response);
        response_pub_->publish(msg);
    }
};

int main(int argc, char**​ argv) {
    rclcpp::init(argc, argv);
    auto server = std::make_shared<FaceControllerServer>();
    server->run();
    rclcpp::shutdown();
    return 0;
}