import argparse
import time
import os
import numpy as np
from PIL import Image
from model import classify_tflite as classify
import tflite_runtime.interpreter as tflite
import platform
from multiprocessing import Pool
from multiprocessing import Manager
import os


def init_interpreter(model_path): # 각 프로세스는 각자의 메모리 공간을 가진다. 객체 서로 공유 불가능. -> 각 프로세스 마다 interpreter 하나씩 만들어 준다.
    global model_load_time, interpreter, input_index

    model_load_time = time.time()
    interpreter = tflite.Interpreter(model_path)
    input_index = interpreter.get_input_details()[0]['index']
    interpreter.allocate_tensors()
    model_load_time = time.time() - model_load_time


def load_data(input_shape):
    load_data = []
    image_path = './dataset/imagenet/imagenet_1000_raw/'
    input_files = os.listdir(image_path)

    for image_file in input_files:
        image = Image.open(image_path+'/'+image_file)
        image = image.convert('RGB').resize([input_shape[1], input_shape[2]], Image.ANTIALIAS)
        image = np.array(image)
        image = np.expand_dims(image, axis=0)
        load_data.append(image)

    return load_data


def inference(image):
    interpreter.set_tensor(input_index, image)
    start = time.perf_counter() 
    interpreter.invoke()
    iter_times.append(time.perf_counter() - start)      
    classes = classify.get_output(interpreter, top_k, threshold)
    
    for klass in classes:
        accuracy.append(klass.score)

    return model_load_time, iter_times, accuracy


def main():
  total_time = time.time()

  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '-m', '--model', required=True, help='File path of .tflite file.')
  parser.add_argument(
      '-k', '--top_k', type=int, default=1,
      help='Max number of classification results')
  parser.add_argument(
      '-t', '--threshold', type=float, default=0.0,
      help='Classification score threshold')
  parser.add_argument(
      '-p', '--processes', type=float, default=1,
      help='Number of using processes')
  args = parser.parse_args()

  global top_k, threshold, iter_times, accuracy

  top_k = args.top_k
  threshold = args.threshold

  interpreter = tflite.Interpreter(args.model) # input shape 알아내기 위해 
  input_shape = interpreter.get_input_details()[0]['shape']
  del interpreter
  
  dataset_load_time=time.time()
  dataset = load_data(input_shape)
  dataset_load_time = time.time() - dataset_load_time
  
  inference_time = time.time()  
  manager = Manager()
  accuracy = manager.list()
  iter_times = manager.list()
  with Pool(processes=num_processes, initializer=init_interpreter, initargs=(args.model,)) as p:
    result = p.map(inference, dataset)   
  inference_time = time.time() - inference_time

  model_load_time = result[-1][0]
  iter_times = result[-1][1]
  accuracy = result[-1][2]

  total_time = time.time() - total_time

  print('***** TF-lite matric *****')
  print('accuracy = {:.3f}'.format(np.sum(accuracy)/(len(dataset)*len(dataset[0]))))
  print('model_load_time = {:.3f}'.format(model_load_time))
  print('dataset_load_time = {:.3f}'.format(dataset_load_time))
  print('inference_time = {:.3f}'.format(inference_time))
  print('inference_time(avg) = {:.3f}'.format(inference_time / (len(dataset)*len(dataset[0]))))
  print('invoke_time(avg) = {:.3f}'.format(np.sum(iter_times) / (len(dataset)*len(dataset[0]))))
  print('IPS = {:.3f}'.format((len(dataset)*len(dataset[0])) / total_time))
  print('IPS(inf) = {:.3f}'.format((len(dataset)*len(dataset[0])) / inferenc_time))
  

if __name__ == '__main__':
  main()
