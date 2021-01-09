#coding: utf-8
import itertools as it
import operator as op
import heapq
import time

#################### read domain ####################
fd = open("test2/test2_domain.txt", 'r')
lines = fd.readlines()
#read types
types = []
for line in lines:
    if "types" in line:
        index = line.find("types") + 6
        line = line[index : -2]
        types = line.split(" ")
        break

#read actions
class Action:
    def __init__(self, name):
        #动作名
        self.name = name
        #[[type,...], [obj,...]
        self.parameters = []
        #[(谓语, [parameter list], 是否有not： True / False), ...]
        self.precondition = {}
        #[(谓语, [parameter list], 是否有not： True / False), ...]
        self.effect = {}

actions = {}

for line_index in range(0, len(lines)):
    if "action" in lines[line_index]:
        #read name
        name = [i for i in lines[line_index].split(" ") if i != ''][-1][ : -1]
        action = Action(name)
        #read parameters
        parameters = [[], []]
        line_index = line_index + 1
        index = lines[line_index].find("(") + 1
        obj_type_list = [i for i in lines[line_index][index : -2].split(" ") if i != '' and i != '-']
        for i in range(0, len(obj_type_list), 2):
            parameters[0].append(obj_type_list[i + 1])
            parameters[1].append(obj_type_list[i][1 : ])
        action.parameters = parameters
        #read precondition
        precondition = []
        line_index = line_index + 1
        index = lines[line_index].find("and ") + 5
        precondition_list = lines[line_index][index : -3].split(") (")
        for pre in precondition_list:
            if "not" not in pre:
                pre_obj_list = pre.split(" ")
                pre_temp = (pre_obj_list[0],[], True)
            else:
                index = pre.find("(") + 1
                pre_obj_list = pre[index : -1].split(" ")
                pre_temp = (pre_obj_list[0] ,[], False)
            for obj in pre_obj_list[ 1 : ]:
                pre_temp[1].append(obj[ 1 : ])
            precondition.append(pre_temp)
        action.precondition = precondition
        #read effect
        effect = []
        line_index = line_index + 1
        index = lines[line_index].find("and ") + 5
        effect_list = lines[line_index][index : -3].split(") (")
        for eff in effect_list:
            if "not" not in eff:
                eff_obj_list = eff.split(" ")
                eff_temp = (eff_obj_list[0], [], True)
            else:
                index = eff.find("(") + 1
                eff_obj_list = eff[index : -1].split(" ")
                eff_temp = (eff_obj_list[0], [], False)
            for obj in eff_obj_list[ 1 : ]:
                eff_temp[1].append(obj[ 1 : ])
            effect.append(eff_temp)
        action.effect = effect

        actions[action.name] = action 

#################### read problem ####################
#fp = open("test4/test4_problem.txt", 'r')
lines = fp.readlines()
#objects {"type": [obj, ...]}
objects = {}
#init state [(谓语, [parameter list], 是否有not： True / False), ...]
init_state = []
#goal state  [(谓语, [parameter list], 是否有not： True / False), ...]
goal_state = []
line_index = 0
while line_index < len(lines):
    #read objects
    if "objects" in lines[line_index]:
        line_index = line_index + 1
        while ")" not in lines[line_index]:
            obj_type_list = [i for i in lines[line_index][ : -1].split(" ") if i != '' and i != '-'] 
            objects[obj_type_list[-1]] = []
            for obj in obj_type_list[ : -1]:
                objects[obj_type_list[-1]].append(obj)
            line_index = line_index + 1
    #read init state
    if "init" in lines[line_index]:
        line_index = line_index + 1
        
        while " )"not in lines[line_index]:
            #空行
            if "(" not in lines[line_index]:
                line_index = line_index + 1
                continue
            #非空行
            left_index = lines[line_index].find('(')
            right_index = lines[line_index].find(')')
            pre_obj_list = lines[line_index][left_index + 1 : right_index].split(" ")
            state = (pre_obj_list[0], [], True)
            for obj in pre_obj_list[ 1 : ]:
                state[1].append(obj) 
            init_state.append(state)
            line_index = line_index + 1
    #read goal state
    if "goal" in lines[line_index]:
        index = lines[line_index].find("and ") + 5
        goal_list = lines[line_index][index : -4].split(") (")
        for goal in goal_list:
            if "not" not in goal:
                goal_obj_list = goal.split(" ")
                goal_temp = (goal_obj_list[0], [], True)
            else:
                index = goal.find("(") + 1
                goal_obj_list = goal[index : -1].split(" ")
                goal_temp = (goal_obj_list[0], [], False)
            for obj in goal_obj_list[ 1 : ]:
                goal_temp[1].append(obj)
            goal_state.append(goal_temp)

    line_index = line_index + 1
"""
print (types)
for a_key in actions.keys():
    print(actions[a_key].name)
    print(actions[a_key].parameters)
    print(actions[a_key].precondition)
    print(actions[a_key].effect)

print (objects)
print (init_state)
print (goal_state)
"""
#################### planner ####################
#比较两个状态是否一样
def is_same_state(state1, state2):
    if state1[0] == state2[0] and op.eq(state1[1],state2[1]):
        return True
    else:
        return False

#比较两个动作是否一样
def is_same_action(action_with_obj1, action_with_obj2):
    if action_with_obj1[0] == action_with_obj2[0] and cmp(action_with_obj1[1], action_with_obj2[1]) == 0:
        return True
    else:
        return False

#判断一个特定动作在当前状态下是否可以执行
def is_available(state, action, action_objs):
    #将action_objs带入action的参数中
    obj_dict = {}
    for i in range(0, len(action.parameters[1])):
        obj_dict[action.parameters[1][i]] = action_objs[i]
    for prec in action.precondition:
        cur_precondition = (prec[0], [obj_dict[x] for x in prec[1]], prec[2])
        #和state判断
        if cur_precondition[2] == True:
            if [is_same_state(s, cur_precondition) for s in state].count(True) == 0:
                return False
        else:
            if [is_same_state(s, cur_precondition) for s in state].count(True) != 0:
                return False
    return True

#得到当前状态下可执行的所有动作
def get_actions_list(state):
    action_list = []
    #对每个动作进行检测
    for a_key in actions.keys():
        #获得该动作对应的所有组成
        all_type_list = []
        same_type_dict = {}
        for obj_type in actions[a_key].parameters[0]:
            all_type_list.append(objects[obj_type])
        all_obj_combination = list(it.product(*all_type_list))
        #对该组成逐个进行检测
        for c in all_obj_combination:
            #根据观察，同类变量不重复
            if len(set(c)) != len(c):
                continue
            if is_available(state, actions[a_key], c):
                action_list.append((a_key, c))
    return action_list

#返回state是否包含了goal_state
def include_goal_state(state, goal_state):
    for goal in goal_state:
        if goal[2] == True:
            if [is_same_state(goal, s) for s in state].count(True) == 0:
                return False
        else:
            if [is_same_state(goal, s) for s in state].count(True) != 0:
                return False    
    return True


#执行动作，忽视Del效果
def take_relax_action(state, action_with_obj):
    obj_dict = {}
    for i in range(0, len(actions[action_with_obj[0]].parameters[1])):
        obj_dict[actions[action_with_obj[0]].parameters[1][i]] = action_with_obj[1][i]
    for eff in actions[action_with_obj[0]].effect:
        cur_eff = (eff[0], [obj_dict[x] for x in eff[1]], eff[2])
        if cur_eff[2] == True and [is_same_state(cur_eff, s) for s in state].count(True) == 0:
            state.append(cur_eff)
    return state

#执行动作
def take_action(state, action_with_obj):
    obj_dict = {}
    for i in range(0, len(actions[action_with_obj[0]].parameters[1])):
        obj_dict[actions[action_with_obj[0]].parameters[1][i]] = action_with_obj[1][i]
    for eff in actions[action_with_obj[0]].effect:
        cur_eff = (eff[0], [obj_dict[x] for x in eff[1]], eff[2])
        if cur_eff[2] == True and [is_same_state(cur_eff, s) for s in state].count(True) == 0:
            state.append(cur_eff)
        if cur_eff[2] == False and [is_same_state(cur_eff, s) for s in state].count(True) != 0:
            del_index = [is_same_state(cur_eff, s) for s in state].index(True)
            del state[del_index]
    return state
#得到特定动作的precondition
def get_relaxed_precondition_with_obj(action_with_obj):
    obj_dict = {}
    for i in range(0, len(actions[action_with_obj[0]].parameters[1])):
        obj_dict[actions[action_with_obj[0]].parameters[1][i]] = action_with_obj[1][i]
    precondition_list = []
    for prec in actions[action_with_obj[0]].precondition:
        if prec[2] == True:
            precondition_list.append((prec[0], [obj_dict[x] for x in prec[1]], prec[2]))
    return precondition_list

#计算松弛问题的状态层集和动作集
def get_relaxed_state_layer(state):
    s = []#存储每一个状态层
    a = []#存储每一层对应的动作集
    total_a = []
    s.append(state)
    index = 0
    while include_goal_state(state, [x for x in goal_state if x[2] == True]) == False:  
        action_list = get_actions_list(state)
        new_action_list = []
        if index == 0:
            new_action_list = action_list[:]
            total_a = action_list[:]
        else:
            for action_with_obj in action_list:
                if [is_same_action(action_with_obj, pre_a) for pre_a in total_a].count(True) == 0:
                    new_action_list.append(action_with_obj)
                    total_a.append(action_with_obj)
        if len(new_action_list) == 0:
            break
        a.append(new_action_list)
        index = index + 1
        cur_state = state[:]
        for action_with_obj in new_action_list:
            cur_state = take_relax_action(cur_state, action_with_obj)
        s.append(cur_state)
        state = cur_state

    return [s, a, index]

def count_action(G, S_set, A_set, k):
    if k == 0:
        return 0
    #划分G
    G_P = []
    G_N = []
    for goal in G:
        if [is_same_state(goal, s) for s in S_set[k - 1]].count(True) == 0:
            G_P.append(goal)
        else:
            G_N.append(goal)
    #找到一个对G_N的极小动作覆盖A
    G_N_action = A_set[k - 1][ : ]
    deleted_index = 0
    while 1 :
        state = []
        deleted_state = []
        for action_with_obj in G_N_action[ : deleted_index] + G_N_action[deleted_index + 1 : ]:
            state = take_relax_action(state, action_with_obj)
            deleted_state = take_relax_action(state, action_with_obj)
        state = take_relax_action(state, G_N_action[deleted_index])
        #若都能覆盖，则去掉动作列表里的一个动作
        if include_goal_state(state, G_N) and include_goal_state(deleted_state, G_N):
            del G_N_action[deleted_index]
            deleted_index = 0
        else:
            deleted_index = deleted_index + 1
        if deleted_index >= len(G_N_action):
            break
    #得到A的precondition
    new_G = G_P[:]
    for action_with_obj in G_N_action:
        precondition_list = get_relaxed_precondition_with_obj(action_with_obj)
        for p in precondition_list:
            if [is_same_state(g, p) for g in new_G].count(True) == 0:
                new_G.append(p)
    return count_action(new_G, S_set, A_set, k - 1) + len(G_N_action)

class PriorityQueue:
    def  __init__(self):
        self.heap = []
        self.count = 0

    def push(self, item, priority):
        entry = (priority, self.count, item)
        heapq.heappush(self.heap, entry)
        self.count += 1

    def pop(self):
        (_, _, item) = heapq.heappop(self.heap)
        return item

    def isEmpty(self):
        return len(self.heap) == 0

    def update(self, item, priority):
        for index, (p, c, i) in enumerate(self.heap):
            if i == item:
                if p <= priority:
                    break
                del self.heap[index]
                self.heap.append((priority, c, item))
                heapq.heapify(self.heap)
                break
        else:
            self.push(item, priority)
            
class PriorityQueueWithFunction(PriorityQueue):
    def  __init__(self, priorityFunction):
        "priorityFunction (item) -> priority"
        self.priorityFunction = priorityFunction      # store the priority function
        PriorityQueue.__init__(self)        # super-class initializer

    def push(self, item):
        "Adds an item to the queue with priority from the priority function"
        PriorityQueue.push(self, item, self.priorityFunction(item))


def a_star_search(init_state, goal_state):
    #node = (state, action_list)
    def f(node):
        g = len(node[1])
        args = get_relaxed_state_layer(node[0])
        h = count_action(args[0][-1], args[0], args[1], args[2])
        return g + h
    frontier = PriorityQueueWithFunction(f)
    start_node = (init_state, [])
    frontier.push(start_node)
    #cycle check
    explored = []

    #iteration
    count = 0
    while not frontier.isEmpty():
        cur_node = frontier.pop()
        if include_goal_state(cur_node[0], goal_state):
            return cur_node[1]

        explored_flag = False
        for e in explored:
            if include_goal_state(e, cur_node[0]) and include_goal_state(cur_node[0], e):
                explored_flag = True
                break
        if explored_flag == False:
            explored.append(cur_node[0])

            action_list = get_actions_list(cur_node[0])

            for action_with_obj in action_list:
                cur_state = cur_node[0][:]
                cur_state = take_action(cur_state, action_with_obj)
                cur_action_list = cur_node[1][:]
                cur_action_list.append(action_with_obj)

                frontier.push((cur_state, cur_action_list))

    return []
starttime = time.time()           
result_list = a_star_search(init_state, goal_state)
endtime = time.time()
if len(result_list) == 0:
    print("no answer")
else:
    for r in result_list:
        print(r)
print("total time = " + str(round(endtime - starttime, 8)) + " secs")      