import torch 
import random 
import numpy as np
from collections import deque
from snake_game_rl import SnakeGameRL, Direction, Point, BLOCK_SIZE
from model import Linear_QNet, QTrainer
from plotter import plot

MAX_MEMORY = 100000
BATCH_SIZE = 1000
LR = 0.001

class Agent:
    def __init__(self):
        self.n_game = 0
        self.epsilon = 0
        self.gamma = 0.9
        
        self.memory = deque(maxlen=MAX_MEMORY)
        
        self.model = Linear_QNet(11, 256, 3)
        # self.model.load_state_dict(torch.load("game136_score72.pth"))
        
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
    
    def get_state(self, game):
        head = game.snake[0]
        
        point_l = Point(head.x - BLOCK_SIZE, head.y)
        point_r = Point(head.x + BLOCK_SIZE, head.y)
        point_u = Point(head.x, head.y - BLOCK_SIZE)
        point_d = Point(head.x, head.y + BLOCK_SIZE)
        
        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN
        
        state = [
            (dir_u and game.is_collision(point_u)) or
            (dir_d and game.is_collision(point_d)) or
            (dir_l and game.is_collision(point_l)) or
            (dir_r and game.is_collision(point_r)),

            (dir_u and game.is_collision(point_r)) or
            (dir_d and game.is_collision(point_l)) or
            (dir_l and game.is_collision(point_u)) or
            (dir_r and game.is_collision(point_d)),

            (dir_u and game.is_collision(point_l)) or
            (dir_d and game.is_collision(point_r)) or
            (dir_r and game.is_collision(point_u)) or
            (dir_l and game.is_collision(point_d)),

            dir_l, dir_r, dir_u, dir_d,

            game.food.x < game.head.x, game.food.x > game.head.x, game.food.y < game.head.y, game.food.y > game.head.y  
        ]
        
        return np.array(state, dtype=int)
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory
        
        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
    
    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)
    
    def get_action(self, state):
        self.epsilon = 80 - self.n_game
        final_move = [0, 0, 0]
        
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            
            final_move[move] = 1
        
        return final_move

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    
    agent = Agent()    
    game = SnakeGameRL()
    
    while True:        
        state_old = agent.get_state(game)
        final_move = agent.get_action(state_old)
        
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)
        
        agent.train_short_memory(state_old, final_move, reward, state_new, done)
        agent.remember(state_old, final_move, reward, state_new, done)
        
        if done:
            game.reset()
            agent.n_game = agent.n_game + 1
            agent.train_long_memory()
            
            if score > record:
                record = score
                agent.model.save(f"game{agent.n_game}_score{record}.pth")
                
            print(f"Game: {agent.n_game}, Score: {score}, Record: {record}")
            
            plot_scores.append(score)
            total_score = total_score + score
            
            mean_score = total_score / agent.n_game
            plot_mean_scores.append(mean_score)
            
            plot(plot_scores, plot_mean_scores)
            
def play():
    record = 0
    
    agent = Agent()
    agent.model.load_state_dict(torch.load("game136_score72.pth"))
    
    game = SnakeGameRL()
    
    while True:
        state = agent.get_state(game)
        
        final_move = [0, 0, 0]
        
        state0 = torch.tensor(state, dtype=torch.float)
        prediction = agent.model(state0)
        move = torch.argmax(prediction).item()    
        final_move[move] = 1
        
        _, done, score = game.play_step(final_move)
        
        if done:
            game.reset()
            agent.n_game = agent.n_game + 1
            
            if score > record:
                record = score
                
            print(f"Game: {agent.n_game}, Score: {score}, Record: {record}")
    

if __name__ == "__main__":
    isTrain = False
    
    if isTrain:
        train()
    else:
        play()