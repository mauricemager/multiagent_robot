import numpy as np
import math
from robot.robot_core import Robot, Robotworld, Landmark
from multiagent.scenario import BaseScenario

class Scenario(BaseScenario):
    def make_world(self):
        # define scenario properties
        num_agents = 1
        num_objects = 1
        num_joints = 2
        arm_length = 0.35
        # create world
        world = Robotworld()

        # add agents
        world.agents = [Robot() for i in range(num_agents)]
        for i, agent in enumerate(world.agents):
            agent.name = 'agent %d' % i
            agent.collide = True
            agent.silent = True

        # add objects
        world.objects = [Landmark() for i in range(num_objects)]
        for i, object in enumerate(world.objects):
            object.name = 'object %d' % i

        # add goals
        world.goals = [Landmark() for i in range(1)]
        for i, goal in enumerate(world.goals):
            goal.name = 'goal'

        world.num_joints = num_joints
        world.arm_length = arm_length

        # reset world
        self.reset_world(world)
        return world

    def reset_world(self, world):
        # set agent properties
        origins = world.robot_position(len(world.agents))
        for i, agent in enumerate(world.agents):
            agent.color = np.array([0.25,0.25,0.25])
            agent.state.lengths = world.arm_length * np.ones(world.num_joints)
            agent.state.angles = (2 * np.random.rand(world.num_joints) - 1) * math.pi
            # agent.state.angles = np.array([0, 0.5]) * math.pi
            agent.state.p_pos = np.array(origins[i][:])

        # set properties for objects
        for i, object in enumerate(world.objects):
            object.color = np.array([0, 0, 1])
            object.state.p_pos = world.random_object_pos()
            # object.state.p_pos = np.array([0.4, 0.4])

        # set properties for goal
        world.goals[0].state.p_pos = world.random_object_pos()
        world.goals[0].color = np.array([1, 0, 0])

    def reward(self, agent, world):
        # reward = 0.0
        # for object in world.objects:
        #     dist2 = np.sum(np.square(object.state.p_pos - world.goals[0].state.p_pos))
        #     reward += dist2
        # return -reward

        # Cartesian reward signal distances
        r_grab, r_goal = 0.0, 0.0
        for i in range(len(agent.state.p_pos)):
            r_grab += np.square(world.objects[0].state.p_pos[i] - agent.get_joint_pos(world.num_joints)[i])
            # print(f"agent.get_joint_pos(world.num_joints) = {agent.get_joint_pos(world.num_joints)}")
            # print(f"position_end_effector(self) = {agent.position_end_effector()}")
            r_goal += np.square(world.goals[0].state.p_pos[i] - world.objects[0].state.p_pos[i])
            # reward += np.square(world.goals[0].state.p_pos[i] - world.objects[0].state.p_pos[i])
        # print(f"sample: np.sqrt(r_grab) = {- np.sqrt(r_grab)}  "
        #       f" and np.sqrt(r_goal) = {-np.sqrt(r_goal)}")
        # reward = np.sqrt(r_grab) + np.sqrt(r_goal)
        return - np.sqrt(r_grab) - 1.5 * np.sqrt(r_goal)






        # # reward based on cartesian coordinates
        # reward = 0.0
        # for i in range(len(agent.state.p_pos)):
        #     reward += np.square(world.goals[0].state.p_pos[i] - world.objects[0].state.p_pos[i])
        # return -np.sqrt(reward)


    def observation(self, agent, world):
        # initialize observation variables
        # state_observations = (agent.state.angles / math.pi).tolist() + [agent.state.grasp]
        goal_obs = world.goals[0].state.p_pos.tolist() # cartesian goal obs
        # goal_obs =
        object_obs = world.objects[0].state.p_pos.tolist() # cartesian obs
        object_dist = []
        partners = []
        state_obs = []
        grasp_obs = [agent.state.grasp]
        for joint in range(1, world.num_joints + 1): # cartesian observation
            state_obs += agent.get_joint_pos(joint).tolist()

        # for joint in range(world.num_joints):
        #     state_obs += [agent.state.angles[joint]]


        # fill in object observation for every object in the environment
        for object in world.objects:
            # determine relative distance to every object in the environment
            dist = np.sum(np.square(object.state.p_pos - agent.position_end_effector()))
            object_dist += [dist]
        # print(f'object_dist test = {object_dist}')
        # when partner agents available, obtain their information
        if len(world.agents) > 1:
            for partner in world.agents:
                # only for partner agents
                if agent.name != partner.name:
                    # determine relative distance to other agent's end effector
                    diff = partner.position_end_effector() - agent.position_end_effector()
                    partners += [np.linalg.norm(diff)] + [partner.state.grasp]
        # combine observations to a single numpy array
        return state_obs + grasp_obs + object_obs + partners + goal_obs
        # return state_obs + grasp_obs + object_dist + partners + goal_obs
        # return state_observations + object_pos + partners + goal_obs


