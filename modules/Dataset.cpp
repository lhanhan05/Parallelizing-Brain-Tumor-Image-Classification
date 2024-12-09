#include <opencv2/opencv.hpp>
using namespace cv;

class Dataset {
public:
    Dataset(vector<std::string> folder_paths, int batch_size) {
        load_images(folder_paths);
        convertImagesToTensor();
        this->batch_size = batch_size;
    }

    void loadImages(vector<std::string> folder_paths) {
        int N = 0;
        for(auto folder_path : folder_paths){
            vector<String> filenames;
            glob(folder_path, filenames, false);

            N += filenames.size();
            

            for (const auto& filename : filenames) {
                Mat img = imread(filename, IMREAD_COLOR);
                if (!img.empty()) {
                    cvtColor(img, img, COLOR_BGR2GRAY);
                    resize(img, img, Size(32, 32));
                    images.push_back(img);
                }
            }
        }

        labels = Tensor<int, 2>(N, 1);
        int i = 0;
        for(auto folder_path : folder_paths){
            vector<String> filenames;
            glob(folder_path, filenames, false);

            for (const auto& filename : filenames) {
                if (filename.find("G") == 0) {
                    labels(i, 0) = 0;
                } else if (filename.find("M") == 0){
                    labels(i, 0) = 1;
                } else if (filename.find("N") == 0){
                    labels(i, 0) = 2;
                } else{ // P
                    labels(i, 0) = 3;
                }
                i+=1;
            }
        }
    }

    void convertImagesToTensor() {
        int N = images.size();
        int C = 1;
        int H = images[0].rows;
        int W = images[0].cols;
        
        img_tensor(N, C, H, W);

        for (int i = 0; i < N; ++i) {
            Mat img = images[i];
            img_tensor.convertTo(img, CV_32F, 1.0 / 255.0);

            for (int h = 0; h < H; ++h) {
                for (int w = 0; w < W; ++w) {
                    img_tensor(i, 0, h, w) = img.at<float>(h, w);
                }
            }
        }
    }

private:
    std::vector<Mat> images;
    int batch_size;

    Tensor<float, 2> labels;
    Tensor<float, 4> img_tensor;
};