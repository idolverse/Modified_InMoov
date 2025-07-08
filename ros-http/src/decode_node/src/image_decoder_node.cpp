#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include <opencv2/opencv.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <iostream>
#include <openssl/bio.h>
#include <openssl/evp.h>

class ImageDecoderNode : public rclcpp::Node {
public:
    ImageDecoderNode() : Node("image_decoder_node") {
        subscription_ = this->create_subscription<std_msgs::msg::String>(
            "/image_raw", 10,
            std::bind(&ImageDecoderNode::callback, this, std::placeholders::_1));
        RCLCPP_INFO(this->get_logger(), "ImageDecoderNode started.");
    }

private:
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;

    void callback(const sensor_msgs::msg::CompressedImage::SharedPtr msg) {
        std::vector<uchar> decoded_bytes = base64_decode(msg->data);

        cv::Mat img = cv::imdecode(msg->data, cv::IMREAD_COLOR);
        if (img.empty()) {
            RCLCPP_ERROR(this->get_logger(), "❌ Failed to decode image. ");
            return;
        }

        cv::imshow("Decoded Image", img);
        cv::waitKey(1);
    }

    std::vector<uchar> base64_decode(const std::string &encoded) {
        BIO *bio, *b64;
        int decodeLen = encoded.length();
        std::vector<uchar> buffer(decodeLen);

        bio = BIO_new_mem_buf(encoded.data(), -1);
        b64 = BIO_new(BIO_f_base64());
        bio = BIO_push(b64, bio);
        BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL); // no newlines

        int length = BIO_read(bio, buffer.data(), decodeLen);
        buffer.resize(length);
        BIO_free_all(bio);
        return buffer;
    }
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ImageDecoderNode>());
    rclcpp::shutdown();
    return 0;
}
