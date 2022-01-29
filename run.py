import gspread
from google.oauth2.service_account import Credentials
import pyinputplus as pyip
import os
from datetime import datetime

# Global Variables for Google API
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]
CREDS = Credentials.from_service_account_file('creds.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('personal-budget')

# Global Variables for app processes
MONTH_NOW = datetime.now().strftime('%B').lower()


class ClearDisplayMixin:
    """
    Mixin to clear terminal screen.
    """
    def clear_display(self):
        os.system('clear')

class UpdateSpreadsheetMixin:
    """
    Mixin for functions related to spreadsheet operations.
    """

    def update_worksheet_cell(self, worksheet, value, row, column):
        """
        Updates Google Sheet worksheet based on present month, value and column arguments.
        """
        print(f"Updating {column} in worksheet...\n")
        month_cell = SHEET.worksheet(worksheet).find(row)
        month_income = SHEET.worksheet(worksheet).find(column)
        SHEET.worksheet(worksheet).update_cell(month_cell.row, month_income.col, value)
        print(f"{column.capitalize()} updated successfully!\n\n")

    def input_values_for_worksheet(self, worksheet):
        """
        Return user input for individual categories.
        """
        self.clear_display()
        spendings = {}
        for item in self.categories_list:
            if item != 'TOTAL' and item!= 'SURPLUS':
                spendings[item] = pyip.inputFloat(prompt=f"\nEnter value for {item}: \n")
            else:
                if item == 'TOTAL':
                    spendings[item] = sum(spendings.values())
                elif item == 'SURPLUS':
                    spendings[item] = self.money - spendings['TOTAL']
        self.clear_display()
        print(f"\nUpdating {worksheet} worksheet with passed values...")
        for key, value in spendings.items():
            key_location = SHEET.worksheet(worksheet).find(key)
            SHEET.worksheet(worksheet).update_cell(key_location.row+1, key_location.col, value)
        print(f"\n{worksheet.capitalize()} worksheet updated successfully!")
        print(f"Your summarize costs for {worksheet} is: {spendings['TOTAL']}")
        
        return spendings

    def clear_cells(self, worksheet, cell):
        print(f"Clearing {worksheet} worksheet...\nIt might take a while...")
        
        SHEET.worksheet(worksheet).batch_clear(["B1:AA1000"])
        # location = SHEET.worksheet(worksheet).find(cell)
        # for i in range (location.col+1,28):
        #     SHEET.worksheet(worksheet).update_cell(location.row, i, "")
        #     SHEET.worksheet(worksheet).update_cell(location.row+1, i, "")
        print(f"\n{worksheet.capitalize()} worksheet is now clear.")

    def update_worksheet_categories(self, categories, worksheet, cell):
        """
        Updates worksheet with categories of user's choice.
        """
        self.clear_display()
        print(f"\nUpdating {worksheet} worksheet...")
        split_categories = categories.split(',')
        month = SHEET.worksheet(worksheet).find(cell)
        for num, item in enumerate(split_categories):
                SHEET.worksheet(worksheet).update_cell(month.row, num+2, item)
        print(f"\n{worksheet.capitalize()} worksheet updated successfully!")
        return split_categories
    
    def create_categories(self, worksheet):
        """
        Gets user input to create peronsalized categories or use default option. Validates inputs.
        """
        self.clear_display()
        options_menu = pyip.inputMenu(['Default', 'Create Categories'], prompt=f"Select how you want to manage your {worksheet.capitalize()}:\n", numbered=True)
        if options_menu == 'Create Categories':
            self.clear_cells(worksheet, 'month')
            print("\nEnter your categories WITHOUT whitespaces such as spaces or tabs and seperated with commas.")
            print("Limit yourself to one word entries only.")
            print("\nExample: Vehicle,Apartment,School,Bank")
            commas = False
            while not commas:
                user_categories = pyip.inputStr(prompt="\nEnter your categories:\n", blockRegexes = ' ')
                if user_categories.find(',') != -1 or user_categories != False:
                    commas = True
                else:
                    print("\nYour inputs must be seperated with commas! Try again.")
            return user_categories + ',TOTAL' + ',SURPLUS'


class Budget(ClearDisplayMixin, UpdateSpreadsheetMixin):
    """
    Budget class that handles user option for calculations.
    """
    def __init__(self):
        self.income = self.enter_income()
        self.plan_elements = self.choose_budget_plan()
        # self.currency = self.choose_currency()
        self.clear_display()
        self.update_worksheet_cell('general', self.income, MONTH_NOW, 'monthly income')
        
    
    def choose_budget_plan(self):
        """
        Gets user input for budget plan based on menu presented on the screen, validates the choice, clears terinal and returns user's choice.
        """
        while True:
            response = pyip.inputMenu(['50/30/20', '70/20/10', 'About plans'], prompt="Please select which budget plan you choose:\n", numbered=True)
            if response == '50/30/20':
                needs = round(self.income * 0.5, 1)
                wants = round(self.income * 0.3, 1)
                savings = round(self.income * 0.2, 1)
                break
            elif response == '70/20/10':
                needs = round(self.income * 0.7, 1)
                wants = round(self.income * 0.2, 1)
                savings = round(self.income * 0.1, 1)
                break
            else:
                self.clear_display()
                print("The 50/30/20 rule is a money management technique that divides your income into three categories:\n50% Needs(essentials)\n30% Wants(non-essentials)\n20% Savings.\n\nBy default this app provides following sub-categories:\nNeeds: Housing, Vehicle costs, Insurance, Food and Banking\nWants: Entertaintment, Wellbeing and Travel\n* Savings is what is meant to be left untouched and used only in case there is absolute need for it. It can cover any unexpected costs.\n\nThe 70/20/10 rule is less robust investment type, where the budget is split in proportion:\n70% Needs\n20% Wants\n10% Savings\n")
        return [response, needs, wants, savings]

    def enter_income(self):
        """
        Gets user's input for income, validates the choice, clears terinal and returns user's choice.
        """
        income = pyip.inputFloat("Enter your monthly income (-TAX): \n")
        return income
    
    def choose_currency(self):
        """
        Gets user's input for currency based on menu presented on the screen, validates the choice, clears terinal and returns user's choice.
        """
        currency = pyip.inputMenu(['PLN', 'EUR', 'GBP', 'USD'], prompt="Enter your currency: \n",  numbered=True)
        return currency

    def manage_your_budget(self, worksheet, surplus, savings):
        """
        Manages SURPLUS values for selected worksheet. Transfer SURPLUS to cell selected by user.
        """
        print("Managing budget...")
        extra_cell = SHEET.worksheet('general').find('extra')
        savings_cell = SHEET.worksheet('general').find('savings')
        surplus_cell = SHEET.worksheet(worksheet).find('SURPLUS')
        if surplus < 0:
            print("Checking possibles to manage your debt...")
            cover = savings + surplus
            if cover < 0:
                print("You don't have enough money for your spends! You must reduce your costs!...")
                quit()
            else:
               SHEET.worksheet(worksheet).update_cell(surplus_cell.row+1, surplus_cell.col, 0) 
               SHEET.worksheet(worksheet).update_cell(savings_cell.row+1, savings_cell.col, cover)
        else:
            add_money = pyip.inputMenu(['Savings', 'Extra Money'], prompt="Select where you want to invest your money:\n", numbered=True)
            if add_money == 'Savings':
                SHEET.worksheet('general').update_cell(savings_cell.row+1, savings_cell.col, savings+surplus)
                SHEET.worksheet(worksheet).update_cell(surplus_cell.row+1, surplus_cell.col, '') 
            else:
                SHEET.worksheet('general').update_cell(extra_cell.row+1, extra_cell.col, surplus)
                SHEET.worksheet(worksheet).update_cell(surplus_cell.row+1, surplus_cell.col, '')
        print("Budget up-to-date!")

    
class Savings(Budget, ClearDisplayMixin):
    """
    Budget child class to handle Savings calculations.
    """
    def __init__(self, money):
        self.money = money
        self.update_worksheet_cell('general', self.money, MONTH_NOW, 'savings')

class Needs(Budget, ClearDisplayMixin, UpdateSpreadsheetMixin):
    """
    Budget child class to handle Needs calculations.
    """
    def __init__(self, money):
        self.money = money
        self.categories_string = self.create_categories('needs')
        self.categories_list = self.update_worksheet_categories(self.categories_string, 'needs', 'month')

class Wants(Budget, ClearDisplayMixin, UpdateSpreadsheetMixin):
    """
    Budget child class to handle Wants calculations.
    """
    def __init__(self, money):
        self.money = money
        self.categories_string = self.create_categories('wants')
        self.categories_list = self.update_worksheet_categories(self.categories_string, 'wants', 'month')    


budget = Budget()
save = Savings(budget.plan_elements[3])

needs = Needs(budget.plan_elements[1])
needs_spendings = needs.input_values_for_worksheet('needs')
needs.manage_your_budget('needs', needs_spendings['SURPLUS'], budget.plan_elements[3])
# wants = Wants(budget.plan_elements[2])
# wants_spendings = wants.input_values_for_worksheet('wants')

