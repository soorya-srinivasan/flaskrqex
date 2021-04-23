"""Define functions to use in redis queue."""

import time

from rq import get_current_job
from PIL import Image
import numpy as np
from keras.models import load_model
import os
from io import BytesIO
import base64
import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Admin123"
)

def predict_func(request_params):
    job = get_current_job()
    #image_path = os.path.abspath(os.path.dirname(__file__)) + '/ISIC_0024329.jpg'
    path = os.path.abspath(os.path.dirname(__file__)) + '/ensemble.h5'
    print(path)
    model = load_model(path)
    print(request_params['img_data'])
    reshaped_image = np.asarray(Image.open(BytesIO(base64.b64decode(request_params['img_data']))).resize((256,192), resample=Image.LANCZOS).convert("RGB"))
    out_vec = np.stack(reshaped_image, 0)
    out_vec = out_vec.astype("float32")
    out_vec /= 255
    out_vec.shape
    oo=out_vec.reshape(1,192, 256,3)
    print(oo.shape)
    outt = np.array(out_vec)
    #print(outt)
    answer = model.predict(oo)
    answer = answer[0].tolist()
    for i in range(len(answer.copy())):
      #print(format(answer[i], '.8f'),end=" ,")
      answer[i] = float(format(answer[i], '.8f'))
    print("list---")
    print(answer)
    aa= max(answer)
    print("max value")
    print(aa)
    name_list = ["Actinic_keratoses","Basal_cell_carcinoma","Benign_keratosis_like_lesions","Dermatofibroma","Melanocytic_nevi","Vascular_lesions","Melanoma"]
    print(answer.index(aa))
    answer_text = name_list[answer.index(aa)]
    
    print()
    mycursor = mydb.cursor()
    query_string = "insert into project.results values(%s,%s,%s,now(),now())"
    print(query_string)
    val = (str(job.id),str(request_params["img_data"]),answer_text)
    mycursor.execute(query_string,val)
    mydb.commit()
    return {
        "job_id": job.id,
        "img": request_params["img_data"],
        "result": answer_text,
    }
