#Libraries
import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

#Constants

#Establishes various education amounts
education_levels = ['High School', 'Associate', 'Bachelor', 'Master', 'PhD']

#Takes education and adds an additional expected age and productivity bonus
education_wage_bonus = {
    'High School': 0,
    'Associate': 10,
    'Bachelor': 25,
    'Master': 45,
    'PhD': 70
}

education_productivity_bonus = {
    'High School': -0.1,
    'Associate': -0.05,
    'Bachelor': 0,
    'Master': 0.1,
    'PhD': 0.15
}

#Creates classes

#Firm class creates the companies the workers work for
class Firm:
    def __init__(self, id, wage_offer):
        self.id = id
        self.wage_offer = wage_offer
        self.employees = []
        self.profit = 0
    
    #Allows firms to hire employees
    def hire(self, worker):
        if worker.accept_job(self):
            self.employees.append(worker)
            return True
        return False
    
    #Makes it so firms are able to adjust their wage offer
    def raise_wage_offer(self):
        self.wage_offer *= 1.05
    
    #Firms can layoff workers if they see too much of a dip in profits        
    def layoff_workers(self, num_to_layoff):
        if len(self.employees) > 0:
            self.employees.sort(key=lambda w: w.productivity)
        
            for i in range(min(num_to_layoff, len(self.employees))):
                worker = self.employees.pop(0)
                worker.employer = None
                worker.employed = 0
    
    #Firms calculate profits to determine success
    def calculate_profit(self):
        revenue = 0
        costs = 0
        for worker in self.employees:
            revenue += (worker.productivity * self.wage_offer)
            costs += worker.reservation_wage
        self.profit = revenue - costs
        return self.profit

#Worker class creates all employees who belong to firms
class Worker:
    def __init__(self, id, education, years_experience):
        self.id = id
        self.education = education
        base_wage = np.round(random.uniform(25,175),2)
        bonus = education_wage_bonus.get(education, 0)
        self.reservation_wage = base_wage + bonus
        self.employer = None
        self.employed = 0
        self.years_experience = years_experience
        productivity = np.round(random.uniform(0.85, 1.15),2)
        education_bonus = education_productivity_bonus.get(education, 0)
        experience_bonus = self.years_experience * 0.01
        self.productivity = productivity + education_bonus + experience_bonus
        self.loyalty = random.uniform(0.5,1)
    
    #Updates the worker at each round in terms of reservation wage and loyalty
    def update_worker(self):
        if self.employed == 0:
            self.reservation_wage *= .95
            self.loyalty -= 0.01
            self.loyalty = max(self.loyalty, 0)
        if self.employed == 1:
            self.reservation_wage *= 1.005
            self.loyalty += 0.01
            self.loyalty = min(self.loyalty, 1.0)
    
    #Workers have the ability to accept a firms job offer
    def accept_job(self, firm):
        if firm.wage_offer >= self.reservation_wage:
            self.employer = firm
            self.employed = 1
            return True
        return False            
    
    #Workers are able to switch to a different firm provided loyalty is low and other firms have better wage offers
    def consider_switching(self, firms):
        if self.employed == 1:          
            switch_probability = (1 - self.loyalty) * 0.1          
            if random.random() < switch_probability:
                better_firms = [f for f in firms if f.wage_offer > self.employer.wage_offer]                
                if better_firms:
                    new_firm = random.choice(better_firms)
                    if self in self.employer.employees:
                        self.employer.employees.remove(self)
                        self.employer = new_firm
                        self.employed = 1
                        new_firm.employees.append(self)
                        return True
        return False
    
    #Ages all workers by 1 month and gives them slightly more productivity for working during that month
    def age_one_period(self):
        self.years_experience += 1/12
        self.productivity *= 1.002
    
    #When a worker reaches 40 years worker, they retire
    def should_retire(self, work_years=40):
        return self.years_experience >= work_years

#Helper Functions

#Picks a randomly distributed education for initialization
def random_education():
    x = random.triangular(0, len(education_levels) - 1, 2)
    return education_levels[round(x)]

#For the hiring phase helps determine how many openings a firm has
def determine_openings(unemployment_rate):     
    if unemployment_rate < 0.04:
        openings = random.randint(0, 1)
    else:
        openings = random.randint(1, 5)
    return openings

#Based on openings, the firm chooses an open candidate and hires them    
def hire_candidates(firm, workers, openings):
    for _ in range(openings):
        unemployed_workers = [w for w in workers if w.employed == 0]
        if not unemployed_workers:
            continue
        candidate = random.choice(unemployed_workers)
        if not firm.hire(candidate):
            firm.raise_wage_offer()

#A firm has the right to layoff workers if they see profits dip to 25% of peak            
def make_layoffs(firm, profit_history):
     max_profit = max(profit_history[firm.id])
     layoff_threshold = max_profit * 0.25
         
     if firm.profit < layoff_threshold and len(firm.employees) > 1:
         num_to_layoff = max(1, len(firm.employees) // 4)
         firm.layoff_workers(num_to_layoff) 

#Ages all workers one round which in the case of this model is one month and ensures old workers retire
def age_workers(workers):
    for worker in workers[:]: 
        worker.age_one_period()
        if worker.should_retire(work_years = 40):
            if worker.employed == 1:
                worker.employer.employees.remove(worker)
            workers.remove(worker)

#When workers retire, new inexperienced workers come in to the work force to replace them
def replace_retirees(workers, initial_worker_count):
    num_retired = initial_worker_count - len(workers)
    for _ in range(num_retired):
        new_worker = Worker(len(workers), random_education(), np.round(random.uniform(0, 5)))
        workers.append(new_worker)                

#Calculates the unemployment rate after every month to analyze how the rate changes
def calculate_unemployment(workers, unemployment_history):
    num_unemployed_final = sum(1 for w in workers if w.employed == 0)
    unemployment_rate = (num_unemployed_final / len(workers))*100
    unemployment_history.append(unemployment_rate)  
              
#Initialization Function

#Creates the environment of firms and workers and sets arbitrary base wage
def create_environment(num_firms, num_workers, min_wage = 70, max_wage = 130, min_experience = 0, max_experieince = 30):
    firms = [Firm(i, np.round(random.uniform(min_wage,max_wage),2)) for i in range (num_firms)]
    workers = [Worker(i, random_education(), np.round(random.uniform(min_experience,max_experieince))) for i in range(num_workers)]
    unemployment_history = []
    profit_history = {firm.id: [] for firm in firms}
    return firms, workers, unemployment_history, profit_history

#Simulation Phase Functions

#Hiring phase allows to hire workers based on available workers and the unemployment rate
def hiring_phase(firms, workers, num_unemployed):
        for firm in firms:
            unemployment_rate = num_unemployed / len(workers)
            openings = determine_openings(unemployment_rate)
            hire_candidates(firm, workers, openings)

#Profits and layoffs phase calculates firms profits and makes layoffs as needed            
def profits_layoffs_phase(firms, profit_history):
    for firm in firms:
        profit = firm.calculate_profit()
        profit_history[firm.id].append(profit)
        make_layoffs(firm, profit_history)

#Update workers updates the workers wage and loyalty and gives a worker the option to quit if they so choose        
def update_workers_phase(workers):
    for w in workers:
         w.update_worker()
         if w.employed == 1 and w.reservation_wage > w.employer.wage_offer:
             if w in w.employer.employees:
                 w.employer.employees.remove(w)
             w.employer = None
             w.employed = 0            

#Workers are able to switch firms during this phase
def job_switching_phase(workers, firms):
    for worker in workers[:]:
        worker.consider_switching(firms)

#Workers are aged at the end of the round and any workers who have retired are replaced by new young workers
def retirement_replacement_phase(workers, initial_worker_count):
    age_workers(workers)
    replace_retirees(workers, initial_worker_count)              

#Runs through the phases of the simulation    
def run_simulation(firms, workers, unemployment_history, profit_history, steps):
    firm_stats_history = []
    for _ in range(steps):
        num_unemployed = sum(1 for w in workers if w.employed == 0)
        initial_worker_count = len(workers)
        
        hiring_phase(firms, workers, num_unemployed)
        profits_layoffs_phase(firms, profit_history)
        update_workers_phase(workers)
        job_switching_phase(workers, firms)
        retirement_replacement_phase(workers, initial_worker_count)
        calculate_unemployment(workers, unemployment_history)
        
        snapshot = {}
        for firm in firms:
            if firm.employees:
                avg_salary = np.mean([w.reservation_wage for w in firm.employees])
                num_workers_f = len(firm.employees)
            else:
                avg_salary = 0.0
                num_workers_f = 0
            snapshot[firm.id] = (num_workers_f, avg_salary)
        firm_stats_history.append(snapshot)    
    
    return firms, workers, unemployment_history, profit_history, firm_stats_history

#Visualization Functions

#Line plot of how unemployment changes over time
def plot_unemployment(unemployment_history):
    plt.plot(range(len(unemployment_history)), unemployment_history)
    plt.xlabel('Round')
    plt.ylabel('Unemployment Rate (%)')
    plt.ylim(0, 105)
    plt.grid(True)
    plt.show()

#Line plot of how firms profits change over time    
def plot_profits(profit_history):
    for firm_id, profits in profit_history.items():
        plt.plot(range(len(profits)), profits, label = f'Firm {firm_id}')

    plt.xlabel('Round')
    plt.ylabel('Profit')
    plt.title('Firm Profits Over Time')
    plt.grid(True)
    plt.show()

#Statistics Function

#Gives important key metreics such as the unemployment rate and firms profits and average salary
def calculate_statistics(firms, workers, unemployment_history, profit_history, firm_stats_history, steps):
    round_steps = [int(i * steps / 10) for i in range(0, 10)]
    round_steps.append(steps - 1)

    for Round in round_steps:
        print(f'\n{"="*70}')
        print(f'After Round {Round}:')
        print(f'{"="*70}')
        print(f'Unemployment Rate: {np.round(unemployment_history[Round], 2)}%\n')
        
        print('FIRM STATISTICS:')
        print(f'{"Firm ID":<10} {"Workers":<10} {"Avg Salary (in 1000s)":<22} {"Profit (in 1000s)":<18}')
        print('-' * 70)
        
        snapshot = firm_stats_history[Round]
        
        for firm in firms:
            num_workers_f, avg_salary = snapshot[firm.id]
            profit = profit_history[firm.id][Round]
            
            print(f'{firm.id:<10} {num_workers_f:<10} ${np.round(avg_salary, 2):<22} ${np.round(profit, 2):<18}')

#Calibration Functions

#Loads in the calibrated data
def load_calibration():
    calibration = pd.read_csv('Calibrated_Employers.csv')
    salary_scale = float(calibration['Salary Scale'].iloc[0])
    return salary_scale

#Based on calibrated data, creates a new calibrated environment
def calibrated_environment(num_firms, num_workers, salary_scale):
    firms = [Firm(i, np.round(random.uniform(70,130) * salary_scale, 2)) for i in range(num_firms)]
    workers = []
    for i in range(num_workers):
        education = random_education()
        years_experience = np.round(random.uniform(0,30), 2)
        w = Worker(i, education, years_experience)
        w.reservation_wage *= salary_scale
        workers.append(w)

    unemployment_history = []
    profit_history = {firm.id: [] for firm in firms}
    return firms, workers, unemployment_history, profit_history
    
#Main Loop

#Runs the calibrated environment, plots proper figures, and calculates labor statistics
if __name__ == '__main__':
    NUM_FIRMS = 30
    NUM_WORKERS = 6000
    STEPS = 1200
    
    salary_scale = load_calibration()
    print(f'Running Calibrated Model with Salary Scale: {salary_scale}')
    
    firms, workers, unemployment_history, profit_history = calibrated_environment(
        NUM_FIRMS, NUM_WORKERS, salary_scale)
    
    firms, workers, unemployment_history, profit_history, firm_stats_history = run_simulation(
        firms, workers, unemployment_history, profit_history, STEPS)
    
    plot_unemployment(unemployment_history)
    plot_profits(profit_history)
    calculate_statistics(firms, workers, unemployment_history, profit_history, firm_stats_history, STEPS)
