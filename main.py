from fastapi import FastAPI, Body, Response, Cookie
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import psycopg2
conn = psycopg2.connect(dbname="emk", host="127.0.0.1", user="emk_u", password="cdjkjxm", port="5432")

import json
import datetime


#app = FastAPI(docs_url=None, redoc_url=None)

app = FastAPI()

link = "127.0.0.1:8000/"
web = "https://peer.websto.pro/"

origins = [
    web,
    "https://91.218.228.110/",
    "https://portal.emk.ru/intranet/peer/peer-ajax.php"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["Content-Type", "Accept", "Location", "Allow", "Content-Disposition", "Sec-Fetch-Dest"],
)



@app.get("/")
def root():
    return RedirectResponse(f"{web}docs")

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
            "cost" : act[2],
            "need_valid" : act[3]
            }
        Activites.append(ac)

    return Activites

@app.post("/change_activities")
def change_activities(data = Body()):

    command = f"UPDATE Activites SET name = \'{data['name']}\', coast = {int(data['cost'])}, need_valid = {data['need_valid']} WHERE Id = {int(data['id'])};"
    print(command)

    cursor = conn.cursor()
    cursor.execute(command)
    conn.commit()

@app.post("/new_activities")
def new_activities(data = Body()):
    name = data['name']
    cost = int(data['cost'])
    need_valid = data['need_valid']
    command = f"INSERT INTO Activites VALUES ((SELECT MAX(Id) + 1 FROM Activites), \'{name}\', {cost}, {need_valid});"
    print(command)

    cursor = conn.cursor()
    cursor.execute(command)
    conn.commit()

#закинь в эксель таблицу
@app.delete("/delete_activities/{active_id}")
def delete_activities(active_id):
    command_1 = f"DELETE FROM ActiveUsers WHERE ActivitesId = {active_id};"
    command_2 = f"DELETE FROM Activites WHERE Id = {active_id};"
    print(command_2)

    cursor = conn.cursor()
    cursor.execute(command_1)
    cursor.execute(command_2)
    conn.commit()
    cursor.close() #помогло?

@app.get("/actions/{uuid}")
def actions(uuid):
    cursor = conn.cursor()
    
    #проверка количества лайков в этом месяце
    command_0 = f"SELECT DATE_PART('month', date_time) FROM activeusers WHERE (uuid_from = \'{uuid}\' AND DATE_PART('month', date_time) = DATE_PART('month', current_date) AND activitesId = 0);"
    cursor.execute(command_0)
    likes = cursor.fetchall()
    like = 10 - len(likes)

    print(like)

    if len(likes) > 10:
        like = 0
    
    #command = f"SELECT Name, Id FROM Activites WHERE user_uuid = \'{uuid}\';"
    command = f"SELECT activites.id, Name FROM Activites JOIN Moder ON ((moder.activeid = activites.id) AND ((moder.user_uuid = \'{uuid}\') OR (moder.user_uuid  = '*')));"
    print(command)

    

    cursor.execute(command)
    activity = cursor.fetchall()

    Activites = []
    for act in activity:
        if act[0] == 0:
            ac = {"id" : act[0], "name" : act[1], "thksLeft" : like}
        else:
            ac = {"id" : act[0], "name" : act[1]}
        Activites.append(ac) 

    return Activites

@app.get("/confirmation/{action_id}/")
def confirmation(action_id):
    command  = f"SELECT activeusers.id, activites.name, activeusers.uuid_from, activeusers.uuid_to, activeusers.description, activeusers.date_time, activites.coast, need_valid FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.valid = 0 AND activites.id = \'{action_id}\');"
    
    print(command)

    cursor = conn.cursor()

    cursor.execute(command)
    activity = cursor.fetchall()

    #cursor.close()
    #conn.close()

    Activites = []
    for act in activity:
        dt = act[5]
        dy = str(dt.day)
        if len(dy) == 1:
            dy='0'+dy
        mns = str(dt.month)
        if len(mns) == 1:
            mns='0'+mns
        ac = {
                "id" : act[0],
                "name" : act[1], 
                "uuid_from" : act[2], 
                "uuid_to" : act[3], 
                "description" : act[4], 
                "date_time" : f"{dt.hour}:{dt.minute} {dy}.{mns}.{dt.year}",
                "cost" : act[6],
                "need_valid" : act[7]
              }
        Activites.append(ac)

    return Activites

@app.get("/do_valid/{action_id}/{uuid}")
def do_valid(action_id, uuid):
    res = False
    command_1 = f"SELECT user_uuid FROM moder WHERE activeid = (SELECT activitesid FROM activeusers WHERE (id = {action_id}));"
    
    command_2 = f"UPDATE ActiveUsers SET valid = 1 WHERE Id = {action_id};"

    cursor = conn.cursor()

    cursor.execute(command_1)
    answer = cursor.fetchall()
    
    for uuids in answer:
        print(uuids[0], uuid)
        if ((str(uuid) == uuids[0]) or (uuid == '1414')) :
            print("###")
            cursor.execute(command_2)
            conn.commit()
            
            res = True

    return res

#обновить в табллице
@app.get("/do_not_valid/{action_id}/{uuid}")
def do_not_valid(action_id, uuid):
    res = False
    command_1 = f"SELECT user_uuid FROM moder WHERE activeid = (SELECT activitesid FROM activeusers WHERE (id = {action_id}));"
    
    command_2 = f"UPDATE ActiveUsers SET valid = 3 WHERE Id = {action_id};"

    cursor = conn.cursor()

    cursor.execute(command_1)
    answer = cursor.fetchall()
    
    for uuids in answer:
        print(uuids[0], uuid)
        if ((str(uuid) == uuids[0]) or (uuid == '1414')) :
            print("###")
            cursor.execute(command_2)
            conn.commit()
            
            res = True

    return res


#обновить в табллице
@app.post("/new_active")
def new_active(data = Body()):
    #добавить ограничение по количеству лайков в месяц
    print(data)

    res = False
    uuid_from = data["uuid_from"]
    uuid_to =  data["uuid_to"]
    action_id = data["act_id"]
    description = data["description"]
    cursor = conn.cursor()

    #проверка количества лайков в этом месяце
    command_0 = f"SELECT DATE_PART('month', date_time) FROM activeusers JOIN activites ON (activeusers.activitesId = activites.id AND activites.need_valid = TRUE AND activeusers.uuid_from = \'{uuid_from}\' AND DATE_PART('month', date_time) = DATE_PART('month', current_date));"
    cursor.execute(command_0)
    likes = cursor.fetchall()
    likes = 10 - len(likes)
    print("Лайков осталось: ", likes)

    if likes < 10:
        return "В этом месяце больше благодарностей оправить нельзя"

    command_1 = f"SELECT Id FROM activites WHERE need_valid = TRUE;"
    cursor.execute(command_1)
    need = cursor.fetchall()
    needs = []
    for nd in need:
        needs.append(nd[0])

    print(action_id, needs)
    if int(action_id) in needs:
        command_2 = f"INSERT INTO ActiveUsers (id, uuid_from, uuid_to, description, activitesId, valid) VALUES ((SELECT MAX(Id)+1 FROM ActiveUsers), \'{uuid_from}\', \'{uuid_to}\', \'{description}\', {action_id}, 0);"
    else:
        command_2 = f"INSERT INTO ActiveUsers (id, uuid_from, uuid_to, description, activitesId, valid) VALUES ((SELECT MAX(Id)+1 FROM ActiveUsers), \'{uuid_from}\', \'{uuid_to}\', \'{description}\', {action_id}, 1);"
    
    

    command_1 = f"SELECT moder.user_uuid FROM moder WHERE (activeid = {action_id});"
    cursor.execute(command_1)
    answer = cursor.fetchone()
    print(answer)
    if answer != "None":
        for uuids in answer:
            print(uuids)
            if ((uuid_from == uuids) or (uuids == '*')):
                print(command_2)
                res = likes
                cursor.execute(command_2)
                conn.commit()
                break
                
    else:
        res = "Нет доступа!"
    
    print(res)
    return res

@app.get("/history_mdr/{action_name}")
def history_mdr(action_name):

    command  = f"SELECT activeusers.id, activeusers.uuid_from, activeusers.uuid_to, activeusers.description, activeusers.valid, activeusers.date_time, activites.coast FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activites.name = \'{action_name}\');"
    
    print(command)

    cursor = conn.cursor()

    cursor.execute(command)
    activity = cursor.fetchall()

    Activites = []
    for act in activity:
        print(act)
        dt = act[5]
        dy = str(dt.day)
        if len(dy) == 1:
            dy='0'+dy
        mns = str(dt.month)
        if len(mns) == 1:
            mns='0'+mns
        st = {
            
            0 : "Не подтверждено", 1 : "Не просмотрено", 2 : "Просмотрено", 3 : "Отказано"}
        ac = {"id" : act[0], "uuid_from" : act[1], "uuid_to" : act[2], "description" : act[3], "stat" : st[act[4]], "date_time" : f"{dt.hour}:{dt.minute} {dy}.{mns}.{dt.year}"}
        Activites.append(ac)

    return Activites

#обновить в табллице
@app.get("/summ/{uuid}")
def summ(uuid):
    try:
        cursor = conn.cursor()

        cursor.execute(f"SELECT SUM(activites.coast) FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND (activeusers.valid = 2 OR activeusers.valid = 1));")
        activity = cursor.fetchone()
        print(activity[0])
        if activity != "None":
            return activity[0]
        else:
            return 0
    except:
        return 0

#обновить в табллице
@app.get("/top")
def top():
    cursor = conn.cursor()

    cursor.execute("SELECT activeusers.uuid_to AS Tabel, SUM(activites.coast) FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND (activeusers.valid = 2 OR activeusers.valid = 1)) GROUP BY activeusers.uuid_to ORDER BY SUM(activites.coast) DESC LIMIT 10;")
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

    print(Activites)
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
    
    cmd = "SELECT * FROM activites"
    cursor.execute(cmd)
    activity = cursor.fetchall()
    res = []
    for act in activity:
        ac = {
            "id" : act[0],
            "name" : act[1],
            "stat" : None
            }
        
        res.append(ac)

    cursor.execute(command)
    activity = cursor.fetchall()
    for act in activity:
        for ac in res:
            
            if str(ac["id"]) == str(act[0]):
                print(ac, act)
                ac["stat"] = act[2]
        
    return res

@app.get("/statistics_history/{action_id}/{uuid}")
def statistics_history(action_id, uuid):

    command = f"SELECT activeusers.id, activeusers.uuid_from, activeusers.description, activeusers.date_time, activites.name, activites.coast, activites.id FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND (activeusers.valid = 2 OR activeusers.valid = 1) AND activites.id = {action_id});"
    
    cursor = conn.cursor()

    cursor.execute(command)
    answer = cursor.fetchall()

    Act = []
    for act in answer:
        dt = act[3]
        dy = str(dt.day)
        if len(dy) == 1:
            dy='0'+dy
        mns = str(dt.month)
        if len(mns) == 1:
            mns='0'+mns
        ac = {
            "id_activeusers" : act[0],
            "uuid" : act[1],
            "descr" : act[2],
            "dt_time" : f"{dt.hour}:{dt.minute} {dy}.{mns}.{dt.year}",
            "category" : act[4],
            "cost" : act[5],
            "id_activites" : act[6]
        }
        Act.append(ac)
    return Act

@app.get("/new_a_week/{uuid}")
def  new_a_month(uuid):
    command_1 = f"SELECT SUM(activites.coast) FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND (SELECT date_trunc('week', NOW())) = (SELECT date_trunc('week', activeusers.date_time)) AND (activeusers.valid = 1 OR activeusers.valid = 2));"
    command_2 = f"SELECT activeusers.id, activeusers.uuid_from, activeusers.description, activeusers.date_time, activites.name, activites.coast, activites.id FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND (SELECT date_trunc('week', NOW())) = (SELECT date_trunc('week', activeusers.date_time)) AND (activeusers.valid = 1 OR activeusers.valid = 2));"

    cursor = conn.cursor()

    cursor.execute(command_1)
    answer = cursor.fetchone()

    sum=0
    for ball in answer:
        sum =  ball
    
    cursor.execute(command_2)
    ans = cursor.fetchall()

    Act=[]
    for act in ans:
        dt = act[3]
        dy = str(dt.day)
        if len(dy) == 1:
            dy='0'+dy
        mns = str(dt.month)
        if len(mns) == 1:
            mns='0'+mns
        ac = {
            "id_activeusers" : act[0],
            "uuid" : act[1],
            "descr" : act[2],
            "dt_time" : f"{dt.hour}:{dt.minute} {dy}.{mns}.{dt.year}",
            "category" : act[4],
            "cost" : act[5],
            "id_activites" : act[6]
        }
        Act.append(ac)
    
    return {"summ" : sum, "activs" : Act}

#внести в таблицу
@app.get("/check/{uuid}")
def check(uuid):
    status = True
    cursor = conn.cursor()
    cursor.execute(f"UPDATE activeusers SET valid = 2 WHERE (uuid_to = \'{uuid}\' AND valid = 1);")
    conn.commit()

    return status

@app.get("/new_activs/{uuid}")
def new_active(uuid):
    command_1 = f"SELECT SUM(activites.coast) FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND activeusers.valid = 1);"
    command_2 = f"SELECT activeusers.id, activeusers.uuid_from, activeusers.description, activeusers.date_time, activites.name, activites.coast, activites.id FROM activeusers JOIN activites ON (activeusers.activitesid = activites.id AND activeusers.uuid_to = \'{uuid}\' AND activeusers.valid = 1);"
    #command_3 = f"UPDATE  activeusers SET valid = 2 WHERE valid = 1 AND activeusers.uuid_to = \'{uuid}\';"
    cursor = conn.cursor()

    cursor.execute(command_1)
    answer = cursor.fetchone()

    sum=0
    for ball in answer:
        sum =  ball
    
    cursor.execute(command_2)
    ans = cursor.fetchall()

    Act=[]
    for act in ans:
        
        dt = act[3]
        dy = str(dt.day)
        if len(dy) == 1:
            dy='0'+dy
        mns = str(dt.month)
        if len(mns) == 1:
            mns='0'+mns
        ac = {
            "id_activeusers" : act[0],
            "uuid" : act[1],
            "descr" : act[2],
            "dt_time" : f"{dt.hour}:{dt.minute} {dy}.{mns}.{dt.year}",
            "category" : act[4],
            "cost" : act[5],
            "id_activites" : act[6]
        }
        Act.append(ac)

    
    
    return {"summ" : sum, "activs" : Act}




@app.get("/get_moders")
def get_moders():
    cursor = conn.cursor()

    cursor.execute("SELECT moder.user_uuid, activites.name, activites.id, activites.coast FROM moder JOIN activites ON activites.id = moder.activeid;")
    activity = cursor.fetchall()

    #cursor.close()
    #conn.close()

    Moders = []
    for mdr in activity:
        md = {
            "moder_id" : mdr[0], 
            "action_name" : mdr[1],
            "action_id" : mdr[2],
            "coast" : mdr[3]
            }
        Moders.append(md)

    return Moders

@app.post("/add_moder/")
def add_moder(data = Body()):
    uuid = data["uuid"]
    actionid = data["actionid"]
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO Moder (Id, user_uuid, activeid) VALUES ((SELECT MAX(id)+1 FROM Moder), \'{uuid}\', {actionid});")
    conn.commit()

@app.delete("/del_moder/{uuid}/{actionid}")
def add_moder(uuid, actionid):
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM Moder WHERE user_uuid = \'{uuid}\' AND activeid = {actionid};")
    conn.commit()



@app.get("/all_admins")
def all_admins():
    adms = open("adms.json", 'r')
    res = json.load(adms)

    return res

@app.post('/new_adm/')
def new_adm(data = Body()):
    uuid = data["uuid"]
    adm_db = open("adms.json", 'r')
    adms = json.load(adm_db)

    dct = {
        "uuid" : uuid
    }

    adms.append(dct)

    adm_db = open("adms.json", 'w')
    json.dump(adms, adm_db)

#закинь в эксель таблицу#закинь в эксель таблицу
@app.delete("/del_adm/{uuid}")
def del_adm(uuid):
    adm_db = open("adms.json", 'r')
    adms = json.load(adm_db)

    dct = []

    for adm in adms:
        if str(adm['uuid']) != uuid:
            print(adm['uuid'], uuid)
            dct.append(adm)
    
    print(adms)

    adm_db = open("adms.json", 'w')
    json.dump(dct, adm_db)
    adm_db.close()



@app.get("/get_uuid")
def get_uuid():
    return {"uuid" : "1414"}



@app.post("/retro")
def retro(data = Body()):
    #собираем запись
    uuid_from = data["uuid_from"]
    uuid_to = data["uuid_to"]
    description =  data["description"]
    valid = 1
    dt_tm = data["date"]
    activitesid = data["activitesid"]

    #проверяем, есть ли такая запись
    excists = False
    cursor = conn.cursor()
    command = f"SELECT id FROM ActiveUsers WHERE ( (activitesid = {activitesid}) AND (description = \'{description}\') AND (uuid_to = \'{uuid_to}\') AND (date_time >= \'{dt_tm}\'::date) AND (date_time < \'{dt_tm}\'::date + \'1 day\'::interval) );"
    print(command)
    cursor.execute(command)
    ans = cursor.fetchall()
    print(ans)

    if ans != []:
        excists = True
    
    if not excists:
        #добавить время
        command = f"INSERT INTO ActiveUsers (id, uuid_from, uuid_to, description, activitesId, date_time, valid) VALUES ((SELECT MAX(Id)+1 FROM ActiveUsers), \'{uuid_from}\', \'{uuid_to}\', \'{description}\', {activitesid}, \'{dt_tm}\', 1)";
        cursor.execute(command)
        conn.commit()

        command = f"SELECT Id FROM ActiveUsers WHERE ( (uuid_from = \'{uuid_from}\') AND (uuid_to = \'{uuid_to}\') AND (description = \'{description}\') AND (activitesId  = {activitesid}) );"
        cursor.execute(command)
        new_id = cursor.fetchone()[0]

        return new_id
    
    else:
        command = f"SELECT Id FROM ActiveUsers WHERE ( (uuid_from = \'{uuid_from}\') AND (uuid_to = \'{uuid_to}\') AND (description = \'{description}\') AND (activitesId  = {activitesid}) );"
        cursor.execute(command)
        new_id = cursor.fetchone()[0]

        return new_id

    #если нет -> вносим
    #cursor = conn.cursor()
    #cursor.execute(f"INSERT INTO Moder (Id, user_uuid, activeid) VALUES ((SELECT MAX(id)+1 FROM Moder), \'{uuid}\', {actionid});")
    #conn.commit()

#conn.autocommit = True
#conn.commit()
