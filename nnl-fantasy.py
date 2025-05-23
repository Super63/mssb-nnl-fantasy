import RioStatLib
import json
import pandas as pd
import os
import csv
import re


# creates usable stats from the json listed
def create_json(file: str):
    with open(file, "r") as jsonStr:
        jsonObj = json.load(jsonStr)
        stats = RioStatLib.StatObj(jsonObj)
    return stats


def winner(event_data):
    last_inn = 1
    last_half = 0
    ascore = 0
    hscore = 0
    homescores = []
    awayscores = []
    max_innings = statfile.inningsPlayed()
    for x in range(1, max_innings * 2 + 1):
        # gets the inning we are lookin for
        if last_half == 1:
            new_inn = last_inn + 1
            new_half = 0
        else:
            new_inn = last_inn
            new_half = 1

        for event in events:
            if new_inn == event["Inning"] and new_half == event["Half Inning"]:
                new_ascore = event["Away Score"]
                new_hscore = event["Home Score"]
        if new_half == 0:
            # walkoff checker (if ending in a walkoff then will allocate the correct score since events dont cover that)
            if last_inn == max_innings:
                homescores.append(statfile.score(0) - hscore)
            else:
                homescores.append(new_hscore - hscore)
            hscore = new_hscore
        else:
            awayscores.append(new_ascore - ascore)
            ascore = new_ascore
        last_inn = new_inn
        last_half = new_half
    away_total = sum(awayscores)
    home_total = sum(homescores)
    inning = max_innings
    # find the inning that the final lead change is made
    if home_total > away_total:
        while home_total > away_total:
            home_total -= homescores[inning - 1]
            away_total -= awayscores[inning - 1]
            inning -= 1
        change_inn = inning + 1
        change_half = 0
    else:
        if away_total > home_total:
            while away_total > home_total:
                home_total -= homescores[inning - 1]
                away_total -= awayscores[inning - 1]
                inning -= 1
        change_inn = inning
        change_half = 1
    if change_inn == 0:
        change_inn += 1
    for event in reversed(event_data):
        found_inn = event["Inning"]
        found_half = event["Half Inning"]
        if found_inn == change_inn and found_half == change_half:
            return [event["Pitch"]["Pitcher Char Id"], event["Pitch"]["Pitcher Team Id"]]
    return "0"


# below via MORI
def track_runs_scored(event_data):
    runner_result_bases = []

    for event in event_data:
        for key, value in event.items():
            if "runner" in key.lower() and isinstance(value, dict):
                runner_result_base = value.get("Runner Result Base")
                hi = ""
                if runner_result_base is not None:
                    if event.get("Half Inning") == 0:
                        hi = "Away"
                    else:
                        hi = "Home"
                    runner_result_bases.append(
                        {
                            "Runner Roster Loc": value.get("Runner Roster Loc"),
                            "Runner Char Id": value.get("Runner Char Id"),
                            "Runner Initial Base": value.get("Runner Initial Base"),
                            "Runner Result Base": value.get("Runner Result Base"),
                            "Half Inning": hi
                        })

    return runner_result_bases


# below via MORI (i edited to be for HR checking)
def hr_fixer(event_data):
    runner_result_bases = []

    for event in event_data:
        for key, value in event.items():
            if "runner" in key.lower() and isinstance(value, dict):
                runner_result_base = value.get("Runner Result Base")
                hi = ""
                if event["Result of AB"] == "HR":
                    if runner_result_base is not None:
                        if event.get("Half Inning") == 0:
                            hi = "Away"
                        else:
                            hi = "Home"
                        runner_result_bases.append(
                            {
                                "Runner Roster Loc": value.get("Runner Roster Loc"),
                                "Runner Char Id": value.get("Runner Char Id"),
                                "Runner Initial Base": value.get("Runner Initial Base"),
                                "Runner Result Base": value.get("Runner Result Base"),
                                "Half Inning": hi
                            })

    return runner_result_bases


def char_team(team: int):
    team_list = []
    for dict in map:
        if team == dict['Owner']:
            team_list.append(dict)
    return team_list


def renameTeam(team: str):
    NNL_list = ["BennyOkay", "Balamb", "Winkly", "Buffcat", "MattGree"
        , "Baltor", "Vickless", "Hellzhero"
        , "Plovely", "Bmills", "Super63", "Nuche"
        , "Cezarito", "Faceman", "Clutch1908"
        , "Flatbread"]
    rio_list = ["bennyokay", "BalambTransfer", "DrWinkly", "Buffcat70", "MattGree"
        , "Baltor33", "VicklessFalcon", "hellzhero"
        , "PLovely28", "RedBonesFan", "Super63", "Nuche17"
        , "Cezarito", "faceman", "Clutch1908"
        , "Flatbread"]
    return NNL_list[rio_list.index(team)]


# gets the stats needed + calcs them (adds a multiplier essentially)
def grab_stats(team: int, character: int, winner_combo: list, player: str):
    # print(team, character)
    char = statfile.characterName(team, character)
    also_team = "bug"
    if team == 0:
        also_team = "Away"
    else:
        also_team = "Home"
    off = statfile.offensiveStats(team, character)
    # print(off)
    # AB
    ab = off["At Bats"]
    # H
    h = off["Hits"]
    # HR
    hr = off["Homeruns"]
    # RBI
    rbi = off["RBI"]
    # SB
    sb = off["Bases Stolen"]
    # R
    r = 0
    for runner in runners:
        if char in runner and character in runner and also_team in runner:
            r += 1
    de = statfile.defensiveStats(team, character)
    # print(de)
    bp = de["Big Plays"]
    ip = 0
    er = 0
    k = 0
    bb = 0
    ha = 0
    if de["Batters Faced"] != 0:
        ip = round(de["Outs Pitched"] / 3, 2)
        er = de["Earned Runs"]
        k = de["Strikeouts"]
        bb = de["Batters Walked"] + de["Batters Hit"]
        ha = de["Hits Allowed"]
    w = 0

    if char == winner_combo[0] and team == winner_combo[1] and de["Outs Pitched"] > 0:
        w += 1
    real_name = char
    if team == 0:
        for duo in away_chars:
            string = duo['Character']
            slice1 = string[0:int(len(string)) - 1]
            slice2 = slice1.replace(" ", "")
            slice3 = slice2.replace("-", "")
            slice4 = re.sub('\d', '', slice3)
            if char.replace(" ", "") == slice4:
                real_name = duo['Character']
                away_chars.pop(away_chars.index({'Character': real_name, 'Owner': aplayer}))
                break
    else:
        for duo in home_chars:
            string = duo['Character']
            slice1 = string[0:int(len(string)) - 1]
            slice2 = slice1.replace(" ", "")
            slice3 = slice2.replace("-", "")
            slice4 = re.sub('\d', '', slice3)
            if char.replace(" ", "") == slice4:
                real_name = duo['Character']
                home_chars.pop(home_chars.index({'Character': real_name, 'Owner': hplayer}))
                break
    stat = {
        "Char": real_name,
        "Team": player,
        "Batting Pos.": character,
        "Hits": h,
        "At Bats": ab,
        'Homeruns': hr,
        "RBIs": rbi,
        "Runs": r,
        "Steals": sb,
        "Big Plays": bp,
        "IP": ip,
        "Earned Runs": er,
        "K's": k,
        "Walks Pitched": bb,
        "Hits Allowed": ha,
        "Wins": w,
    }
    statistics.append(stat)
    return


with open('C:/Users/super/PycharmProjects/mssbfantasy/NNL_Fantasy_Character_Mapping.csv', 'r') as file:
    csv_reader = csv.DictReader(file)
    map = [row for row in csv_reader]
    # print(map)

directory = "C:/Users/super/OneDrive/Desktop/directoryOfStatfiles"
for filename in os.listdir(directory):
    stat_file = os.path.join(directory, filename)
    # checking if it is a file
    if (os.path.isfile(stat_file)) & (filename != ".DS_Store") & ('decoded' in filename):
        with open(stat_file, "r") as stats:
            jsonObj = json.load(stats)
            statfile = RioStatLib.StatObj(jsonObj)
    statistics = []
    jason = "file-goes-here.json"
    aplayer = renameTeam(statfile.player(0))
    away_chars = char_team(aplayer)
    hplayer = renameTeam(statfile.player(1))
    home_chars = char_team(hplayer)
    events = statfile.events()
    runs_scored = track_runs_scored(events)
    # print(runs_scored)
    runners = []
    runners_loc = []
    winner_id_team = winner(events)
    for i in runs_scored:
        if i['Runner Result Base'] == 4:
            runners.append({i['Runner Char Id'], i['Runner Roster Loc'], i["Half Inning"]})

    for i in hr_fixer(events):
        runners.append({i['Runner Char Id'], i['Runner Roster Loc'], i["Half Inning"]})
    # print(runners)

    for team in range(0, 2):
        if team == 0:
            user = aplayer
        else:
            user = hplayer
        for character in range(0, 9):
            grab_stats(team, character, winner_id_team, user)
    # print(statistics)

    df = pd.DataFrame(statistics)
    output = aplayer + "@" + hplayer
    df.to_csv(directory + "/" + output)

    # todo
    # Add .csv to file extentions
