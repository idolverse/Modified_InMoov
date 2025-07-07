#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/compressed_image.hpp"
#include <opencv2/opencv.hpp>
#include <vector>

class ImageDecoderNode : public rclcpp::Node {
public:
    ImageDecoderNode() : Node("image_decoder_node") {
        subscription_ = this->create_subscription<sensor_msgs::msg::CompressedImage>(
            "/image_raw", 10,
            std::bind(&ImageDecoderNode::callback, this, std::placeholders::_1));
        RCLCPP_INFO(this->get_logger(), "✅ ImageDecoderNode started, listening to /image_raw");
    }

private:
    rclcpp::Subscription<sensor_msgs::msg::CompressedImage>::SharedPtr subscription_;

    void callback(const sensor_msgs::msg::CompressedImage::SharedPtr msg) {
        cv::Mat img = cv::imdecode(cv::Mat(msg->data), cv::IMREAD_COLOR);
        if (img.empty()) {
            RCLCPP_ERROR(this->get_logger(), "❌ Failed to decode CompressedImage");
            return;
        }

        cv::imshow("Decoded Image", img);
        cv::waitKey(1);
    }
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ImageDecoderNode>());
    rclcpp::shutdown();
    return 0;
}
