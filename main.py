from fastapi import FastAPI, Body, Response, Cookie
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import psycopg2
conn = psycopg2.connect(dbname="emk", host="127.0.01", user="emk_u", password="cdjkjxm", port="5432")

import json
import datetime



app = FastAPI()

app.mount("/static", StaticFiles(directory="public", html=True))
#app.mount("/static", StaticFiles(directory="/", html=True))

origins = [
    "http://192.168.222.130",
    "http://localhost:8000",
    "http://www.emk.like.ru",
    "http://emk.like.ru"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],#, "OPTIONS", "DELETE", "PATH", "PUT"],
    allow_headers=["Content-Type", "Accept", "Location", "Allow", "Content-Disposition", "Sec-Fetch-Dest"],
)



@app.get("/")
def root():
    return FileResponse("public/index.html")

@app.get("/index")
def root():
    return RedirectResponse("/")



@app.get("/activites")
def activites():
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Activites;")
    activity = cursor.fetchall()

    #cursor.close()
    #conn.close()

    Activites = []
    for act in activity:
        ac = {
            "id" : act[0], 
            "name" : act[1],
            "coast" : act[2], 
            "user_uuid" : act[3]
            }
        Activites.append(ac)

    return Activites

@app.post("/change_activities")
def change_activities(data = Body()):

    command = f"UPDATE Activites SET name = \'{data['name']}\', coast = {int(data['coast'])}, user_uuid = \'{data['user_uuid']}\' WHERE Id = {int(data['id'])};"
    print(command)

    cursor = conn.cursor()
    cursor.execute(command)
    conn.commit()

@app.post("/new_activities")
def new_activities(data = Body()):
    
    command = f"INSERT INTO Activites VALUES ((SELECT MAX(Id) + 1 FROM Activites), \'{data['name']}\', {int(data['coast'])}, \'{data['user_uuid']}\');"
    print(command)

    cursor = conn.cursor()
    cursor.execute(command)
    conn.commit()

@app.get("/delete_activities/{active_id}")
def delete_activities(active_id):
    command = f"DELETE FROM Activites WHERE Id = {active_id};"
    print(command)

    cursor = conn.cursor()
    cursor.execute(command)
    conn.commit()

@app.get("/actions/{uuid}")
def actions(uuid):
    command = f"SELECT Name, Id FROM Activites WHERE user_uuid = \'{uuid}\';"
    print(command)

    cursor = conn.cursor()

    cursor.execute(command)
    activity = cursor.fetchall()

    Activites = []
    for act in activity:
        ac = {"id" : act[1], "name" : act[0]}
        Activites.append(ac) 

    return Activites

@app.get("/confirmation/{name}/")
def confirmation(name):
    command  = f"SELECT activeusers.id, activeusers.uuid_from, activeusers.uuid_to, activeusers.description, activeusers.date_time, activites.coast, activites.user_uuid FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.valid = 0 AND activites.name = \'{name}\');"
    
    print(command)

    cursor = conn.cursor()

    cursor.execute(command)
    activity = cursor.fetchall()

    #cursor.close()
    #conn.close()

    Activites = []
    for act in activity:
        dt = act[4]
        ac = {"id" : act[0], "uuid_from" : act[1], "uuid_to" : act[2], "description" : act[3], "date_time" : f"{dt.hour}:{dt.minute} {dt.day}.{dt.month}.{dt.year}"}
        Activites.append(ac)

    return Activites

@app.get("/do_valid/{action_id}/{uuid}")
def do_valid(action_id, uuid):
    res = False
    command_1 = f"SELECT activites.user_uuid FROM activites WHERE name = (SELECT activites.name FROM activites JOIN activeusers ON (activeusers.activitesid = activites.id AND activeusers.id = {action_id}) );"
    
    command_2 = f"UPDATE ActiveUsers SET valid = 1 WHERE Id = {action_id};"

    cursor = conn.cursor()

    cursor.execute(command_1)
    answer = cursor.fetchall()
    for uuids in answer:
        if uuid == uuids[0]:
            cursor.execute(command_2)
            conn.commit()
            
            res = True

    return res

@app.get("/do_not_valid/{action_id}/{uuid}")
def do_not_valid(action_id, uuid):
    res = False
    command_1 = f"SELECT activites.user_uuid FROM activites WHERE name = (SELECT activites.name FROM activites JOIN activeusers ON (activeusers.activitesid = activites.id AND activeusers.id = {action_id}) );"
    
    command_2 = f"UPDATE ActiveUsers SET valid = 3 WHERE Id = {action_id};"

    cursor = conn.cursor()

    cursor.execute(command_1)
    answer = cursor.fetchall()
    for uuids in answer:
        if (uuid == uuids[0]):
            cursor.execute(command_2)
            conn.commit()
            
            res = True

    return res

@app.post("/new_active")
def new_active(data = Body()):
    res = False
    uuid_from = data["uuid_from"]
    uuid_to =  data["uuid_to"]
    action_id = data["act_id"]
    description = data["description"]

    command_1 = f"SELECT activites.user_uuid FROM activites WHERE name = (SELECT activites.name FROM activites JOIN activeusers ON (activeusers.activitesid = activites.id AND activeusers.id = {action_id}) );"

    command_2 = f"INSERT INTO ActiveUsers (id, uuid_from, uuid_to, description, activitesId) VALUES ((SELECT MAX(Id)+1 FROM ActiveUsers), \'{uuid_from}\', \'{uuid_to}\', \'{description}\', {action_id});"

    cursor = conn.cursor()

    cursor.execute(command_1)
    answer = cursor.fetchall()
    for uuids in answer:
        if (uuid_from == uuids[0]):
            cursor.execute(command_2)
            conn.commit()

            res = True

        elif action_id == 1:
            cursor.execute(command_2)
            conn.commit()

            res = False
    
    return res

@app.get("/history_mdr/{action_name}")
def history_mdr(action_name):

    command  = f"SELECT activeusers.id, activeusers.uuid_from, activeusers.uuid_to, activeusers.description, activeusers.valid, activeusers.date_time, activites.coast, activites.user_uuid FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activites.name = \'{action_name}\');"
    
    print(command)

    cursor = conn.cursor()

    cursor.execute(command)
    activity = cursor.fetchall()

    Activites = []
    for act in activity:
        print(act)
        dt = act[5]
        st = {0 : "Не подтверждено", 1 : "Не просмотрено", 2 : "Просмотрено", 3 : "Отказано"}
        ac = {"id" : act[0], "uuid_from" : act[1], "uuid_to" : act[2], "description" : act[3], "stat" : st[act[4]], "date_time" : f"{dt.hour}:{dt.minute} {dt.day}.{dt.month}.{dt.year}"}
        Activites.append(ac)

    return Activites

@app.get("/summ/{uuid}")
def summ(uuid):
    cursor = conn.cursor()

    cursor.execute(f"SELECT SUM(activites.coast) FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND (activeusers.valid = 2 OR activeusers.valid = 1));")
    activity = cursor.fetchone()

    return activity[0]

@app.get("/top")
def top():
    cursor = conn.cursor()

    cursor.execute("SELECT activeusers.uuid_to AS Tabel, SUM(activites.coast) FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND (activeusers.valid = 2 OR activeusers.valid = 1)) GROUP BY activeusers.uuid_to ORDER BY SUM(activites.coast) DESC LIMIT 20;")
    activity = cursor.fetchall()

    Activites = []
    i=0
    for act in activity:
        i+=1
        ac = {
            "place" : i,
            "uuid" : act[0], 
            "sum" : act[1]
            }
        Activites.append(ac)

    return Activites

@app.get("/my_place/{uuid}")
def my_place(uuid):
    command = "SELECT ROW_NUMBER() OVER( ORDER BY SUM(activites.coast) DESC) AS num, activeusers.uuid_to AS User, SUM(activites.coast) FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND (activeusers.valid = 2 OR activeusers.valid = 1)) GROUP BY activeusers.uuid_to ORDER BY SUM(activites.coast) DESC;"

    cursor = conn.cursor()
    cursor.execute(command)
    activity = cursor.fetchall()
    res = "Либо Вы вне всяких оценок, либо ВЫ ЕЩЁ СПИТЕ!"
    for act in activity:
        if act[1] == uuid:
            res = act[0]

    return res

@app.get("/statistics/{uuid}")
def statistics(uuid):
    command = f"SELECT activites.id, activites.name, SUM(activites.coast) AS SummTable FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND (activeusers.valid = 2 OR activeusers.valid = 1)) GROUP BY activites.name, activites.id;"
    
    cursor = conn.cursor()
    cursor.execute(command)
    activity = cursor.fetchall()
    Act = []
    for act in activity:
        ac = {
            "id" : act[0],
            "name" : act[1],
            "stat" : act[2]
            }
        Act.append(ac)
    return Act

@app.get("/statistics_history/{action_id}/{uuid}")
def statistics_history(action_id, uuid):

    command = f"SELECT activeusers.id, activeusers.uuid_from, activeusers.description, activeusers.date_time, activites.name, activites.coast, activites.id FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND (activeusers.valid = 2 OR activeusers.valid = 1) AND activites.id = {action_id});"

    cursor = conn.cursor()

    cursor.execute(command)
    answer = cursor.fetchall()

    Act = []
    for act in answer:
        ac = {
            "id_activeusers" : act[0],
            "uuid" : act[1],
            "discr" : act[2],
            "dt_time" : act[3],
            "category" : act[4],
            "coast" : act[5],
            "id_activites" : act[6]
        }
        Act.append(ac)
    return Act
    




#conn.autocommit = True
#conn.commit()