import numpy as np
import math
from robot.robot_core import Robot, Robotworld, Landmark
# from multiagent.core import Landmark
from multiagent.scenario import BaseScenario

class Scenario(BaseScenario):
    def make_world(self):
        # define scenario properties
        num_agents = 2
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
            object.collide = True
            object.movable = True

        # add goals
        world.goals = [Landmark() for i in range(1)]
        for i, goal in enumerate(world.goals):
            goal.name = 'goal'
            goal.collide = False
            goal.movable = False

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
            agent.state.p_pos = np.array(origins[i][:])

        # set properties for landmarks
        for i, object in enumerate(world.objects):
            object.color = np.array([1, 0, 0])
            object.state.p_pos = 0.2 * np.random.randn(world.dim_p) + np.array([0.5, 0.0])

        # set properties for goal
        world.goals[0].state.p_pos = - world.objects[0].state.p_pos
        # world.goals[0].state.p_vel = np.zeros(world.dim_p)

    def reward(self, agent, world):
        reward = 0.0
        for object in world.objects:
            dist2 = np.sum(np.square(object.state.p_pos - world.goals[0].state.p_pos))
            reward += dist2
        return -reward

    def observation(self, agent, world):
        # initialize observation variables
        state_observations = (agent.state.angles / math.pi).tolist() + [agent.state.grasp]
        object_pos = []
        partners = []
        # fill in object observation for every object in the environment
        for object in world.objects:
            # determine relative distance to every object in the environment
            dist = np.sum(np.square(object.state.p_pos - agent.position_end_effector()))
            object_pos += [dist]
        # when partner agents available, gain their information
        if len(world.agents) > 1:
            for partner in world.agents:
                # only for partner agents
                if agent.name != partner.name:
                    # determine relative distance to other agent's end effector
                    diff = partner.position_end_effector() - agent.position_end_effector()
                    partners += [np.linalg.norm(diff)] + [partner.state.grasp]
        # combine observations to a single numpy array
        return state_observations + object_pos + partners

