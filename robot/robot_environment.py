from multiagent.multi_discrete import MultiDiscrete
from multiagent.environment import MultiAgentEnv
import numpy as np

# environment for all agents in the multiagent world
# currently code assumes that no agents will be created/destroyed at runtime!
class RobotEnv(MultiAgentEnv):
    def __init__(self, *args, **kwargs):
        super(RobotEnv, self).__init__(*args, **kwargs)
        self.discrete_action_space = False


    def _set_action(self, action, agent, action_space, time=None):
        agent.action.u = np.zeros(self.world.dim_p + 1) # ANDERS
        agent.action.c = np.zeros(self.world.dim_c)
        # process action
        if isinstance(action_space, MultiDiscrete):
            act = []
            size = action_space.high - action_space.low + 1
            index = 0
            for s in size:
                act.append(action[index:(index+s)])
                index += s
            action = act
        else:
            action = [action]

        if agent.movable:
            # physical action
            if self.discrete_action_input:
                agent.action.u = np.zeros(self.world.dim_p)
                # process discrete action
                if action[0][1] == 1: agent.action.u[0] = +1.0
                if action[0][2] == 1: agent.action.u[0] = -1.0
                if action[0][3] == 1: agent.action.u[1] = +1.0
                if action[0][4] == 1: agent.action.u[1] = -1.0
                agent.state.grasp = action[0][5] == 1.0
            else:
                if self.force_discrete_action:
                    d = np.argmax(action[0])
                    action[0][:] = 0.0
                    action[0][d] = 1.0
                if self.discrete_action_space:
                    agent.action.u[0] += action[0][1] - action[0][2]
                    agent.action.u[1] += action[0][3] - action[0][4]
                    agent.action.u[-1] = action[0][5]
                else:
                    agent.action.u = action[0]
            sensitivity = 1.0
            if agent.accel is not None:
                sensitivity = agent.accel
            agent.action.u *= sensitivity
            action = action[1:]
        if not agent.silent:
            # communication action
            if self.discrete_action_input:
                agent.action.c = np.zeros(self.world.dim_c)
                agent.action.c[action[0]] = 1.0
            else:
                agent.action.c = action[0]
            action = action[1:]
        # make sure we used all elements of action
        assert len(action) == 0

    # render environment
    def render(self, mode='human'):
        if mode == 'human':
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            message = ''
            for agent in self.world.agents:
                comm = []
                for other in self.world.agents:
                    if other is agent: continue
                    if np.all(other.state.c == 0):
                        word = '_'
                    else:
                        word = alphabet[np.argmax(other.state.c)]
                    message += (other.name + ' to ' + agent.name + ': ' + word + '   ')
            # print(message)


        for i in range(len(self.viewers)):
            # create viewers (if necessary)
            if self.viewers[i] is None:
                # import rendering only if we need it (and don't import for headless machines)
                #from gym.envs.classic_control import rendering
                from multiagent import rendering
                self.viewers[i] = rendering.Viewer(700,700)

        results = []
        for i in range(len(self.viewers)):
            from multiagent import rendering
            # update bounds to center around agent
            cam_range = 1
            if self.shared_viewer:
                pos = np.zeros(self.world.dim_p)
            else:
                pos = self.agents[i].state.p_pos
            self.viewers[i].set_bounds(pos[0]-cam_range,pos[0]+cam_range,pos[1]-cam_range,pos[1]+cam_range)
            # update geometry positions
            self.render_geoms = []
            for e, entity in enumerate(self.world.entities):
                if 'agent' in entity.name:
                    geom = rendering.make_polyline(entity.create_robot_points(shorter_end=True))
                    geom.set_color(*entity.color, alpha=0.5)
                    geom.set_linewidth(5)
                    gripper = rendering.make_polyline(entity.create_gripper_points(gripped=entity.state.grasp))
                    gripper.set_color(*entity.color, alpha=0.5)
                    gripper.set_linewidth(5)
                    self.render_geoms.append(geom)
                    self.render_geoms.append(gripper)

                elif 'object' in entity.name:
                    geom = rendering.make_polygon(entity.create_object_points())
                    geom.set_color(*entity.color)
                    self.render_geoms.append(geom)
                else:
                    geom = rendering.make_polygon(entity.create_goal_points())
                    self.render_geoms.append(geom)

            for viewer in self.viewers:
                viewer.geoms = []
                # print(self.render_geoms)
                for geom in self.render_geoms:
                    viewer.add_geom(geom)

            # render to display or array
            results.append(self.viewers[i].render(return_rgb_array = mode=='rgb_array'))

        return results
