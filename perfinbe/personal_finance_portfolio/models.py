from django.db import models

# Create your models here.
# personal_finance_portfolio/models.py

from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class AssetClass(models.Model):
    # Define the asset classes
    #Equity Funds/ETFs: Some of this information could be derived; however for now explicty adding
    DOMESTIC_EQUITY = 'Domestic Equity'
    INTERNATIONAL_EQUITY = 'International Equity'
    GLOBAL_EQUITY = 'Global Equity'
    # Fixed Income Funds/ETF's
    GOVERNMENT_BONDS = 'Government Bonds'
    CORPORATE_BONDS = 'Corporate Bonds'
    MUNICIPAL_BONDS = 'Municipal Bonds'
    #Misc
    BALANCED_FUNDS = 'Balanced Funds'
    ALTERNATIVE_FUNDS = 'Alternative Funds' # Commodities, Realestate
    
    ASSET_CHOICES = [
        (DOMESTIC_EQUITY, 'Domestic Equity'),
        (INTERNATIONAL_EQUITY, 'International Equity'),
        (GLOBAL_EQUITY, 'Global Equity'),
        (GOVERNMENT_BONDS, 'Government Bonds'),
        (CORPORATE_BONDS, 'Corporate Bonds'),
        (MUNICIPAL_BONDS, 'Municipal Bonds'),
        (BALANCED_FUNDS, 'Balanced Funds'),
        (ALTERNATIVE_FUNDS, 'Alternative Funds'),
    ]    
    name = models.CharField(max_length=50, choices=ASSET_CHOICES, primary_key=True)

    def __str__(self):
        return self.name

class InvestmentStyle(models.Model):
    # Define the investment style

    GROWTH = 'Growth'
    VALUE = 'Value'
    BLEND_CORE = 'Blend/Core'

    INVESTMENT_STYLE_CHOICES = [
        (GROWTH, 'Growth'),
        (VALUE, 'Value'),
        (BLEND_CORE, 'Blend/Core'),
    ]    
    name = models.CharField(max_length=50, choices=INVESTMENT_STYLE_CHOICES, primary_key=True)

    def __str__(self):
        return self.name

class GeographicFocus(models.Model):
    # Define the geographical focus
    ASIA = 'ASIA'
    EUROPE = 'Europe'
    LATIN_AMERICA = 'Latin America'
    CHINA = 'China'
    US = 'US'
    
    GEOGRAPHICAL_CHOICES = [
        (ASIA, 'Asia'),
        (EUROPE, 'Europe'),
        (LATIN_AMERICA, 'Latin America'),
        (CHINA, 'China'),
        (US, 'US'),
    ]

    name = models.CharField(max_length=50, choices=GEOGRAPHICAL_CHOICES, primary_key=True)

    def __str__(self) -> str:
        return self.name

class SectorIndustryFocus(models.Model):
    # Define the Sector and Industry Focus
    TECHNOLOGY = 'Technology'
    HEALTHCARE = 'Healthcare'
    FINANCIALS = 'Financials'
    ENERGY = 'Energy'
    CONSUMER_DISCRETIONARY = 'Consumer Discretionary'
    CONSUMER_STAPLES = 'Consumer Staples'
    UTILITIES = 'Utilities'
    REAL_ESTATE = 'Real Estate'
    INSUSTRIALS = 'Industrials'
    MATERIALS = 'Materials'
    TELECOMMUNICATIONS = 'Telecommunications'

    SECTOR_INDUSTRY_CHOICES = [
        (TECHNOLOGY, 'Technology'),
        (HEALTHCARE, 'Healthcare'),
        (FINANCIALS, 'Financials'),
        (ENERGY, 'Energy'),
        (CONSUMER_DISCRETIONARY, 'Consumer Discretionary'),
        (CONSUMER_STAPLES, 'Consumer Staples'),
        (UTILITIES, 'Utilities'),
        (REAL_ESTATE, 'Real Estate'),
        (INSUSTRIALS, 'Industrials'),
        (MATERIALS, 'Materials'),
        (TELECOMMUNICATIONS, 'Telecommunications'),      
    ]

    name = models.CharField(max_length=50, choices=SECTOR_INDUSTRY_CHOICES, primary_key=True)

    def __str__(self) -> str:
        return self.name

class Investment(models.Model):
    """
    Represents an investment. This will be the master for any particular investment no matter transaction or portfolio.
    PortfolioInvestment will be the portfolio representation of this investment and Transaction will be the transaction representation of this investment.

    Attributes:
        symbol (str): The symbol, ticker symbol of the investment.
        name (str): The name of the investment.
        - removing investment type, using this as the base class and having classes for the different investment type
            investment_type (str): The type of investment (e.g., 'stock', 'etf').
    """

    ticker_symbol = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    name = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(Category, through='InvestmentCategory')

    def __str__(self):
        return self.name

class InvestmentCategory(models.Model):
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = (('investment', 'category'),)

    def __str__(self):
        return f"{self.investment.name} - {self.category.name}"


class Stock(Investment):
    #categories = models.ManyToManyField(InvestmentCategory)
    company_name = models.CharField(max_length=100)
    dividend_yield = models.DecimalField(max_digits=5, decimal_places=2)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2)
    pe_ratio = models.DecimalField(max_digits=5, decimal_places=2)
    beta = models.DecimalField(max_digits=5, decimal_places=2)
"""
class ETF(Investment):
    categories = models.ManyToManyField(Category, through='InvestmentCategory')

class MutualFund(Investment):
    categories = models.ManyToManyField(Category, through='InvestmentCategory')

class Bond(Investment):
    categories = models.ManyToManyField(Category, through='InvestmentCategory')
    maturity_date = models.DateField()
    coupon_rate = models.DecimalField(max_digits=5, decimal_places=2)
"""
class InvestmentPlatform(models.Model):
    """
    Represents an investment platform.

    Attributes:
        name (str): The name of the investment platform.
    """
    WELLS_FARGO = 'Wells Fargo'
    ETRADE = 'Etrade'
    FIDELITY = 'Fidelity'
    SCHWAB = 'Schwab'
    PRINCIPAL = 'Principal'
    PROSPER = 'Prosper'
    NATIONWIDE = 'Nationwide'
    PLATFORM_CHOICES = [
        (WELLS_FARGO, 'Wells Fargo'),
        (ETRADE, 'Etrade'),
        (FIDELITY, 'Fidelity'),
        (NATIONWIDE, 'Nationwide'),
        (SCHWAB, 'Schwab'),
        (PRINCIPAL, 'Principal'),
        (PROSPER, 'Prosper'),
    ]

    name = models.CharField(max_length=100, choices=PLATFORM_CHOICES, primary_key=True)
    website = models.URLField(blank=True)

    def save(self, *args, **kwargs):
        platform_to_website = {
            'Wells Fargo': 'https://www.wellsfargo.com/',
            'Etrade': 'https://us.etrade.com/home',
            'Fidelity': 'https://www.fidelity.com/',
            'Nationwide': 'https://login.nationwide.com/access/web/login.htm',
            'Schwab': 'https://www.schwab.com/',
            'Principal': 'https://www.principal.com/',
            'Prosper': 'https://www.prosper.com/',
        }

        if self.name in platform_to_website:
            self.website = platform_to_website[self.name]

        super().save(*args, **kwargs)        

    def __str__(self):
        return self.name


class BrokerageAccountType(models.Model):
    """
    Represents a type of portfolio.

    Attributes:
        name (str): The name of the portfolio type.
    """
    RETIREMENT_CHOICES = [('401K', '401k'), ('403b', '403b'), ('ROTH 401K', 'ROTH 401K'), ('Traditional IRA', 'Traditional IRA'), ('Roth IRA', 'Roth IRA'), ('HSA', 'HSA'), ('SEP IRA', 'SEP IRA'), ('Annuity', 'Annuity'), ('Defered Compensation', 'Defered Compensation')]
    BROKERAGE_CHOICES = [('Taxable', 'Taxable'), ('RSU', 'RSU'), ('ESPP', 'ESPP'), ('ESPP & RSU', 'ESPP & RSU'), ('Trust', 'Trust'), ('529', '529'), ('Custodial UTMA', 'Custodial UTMA'), ('Custodial UGMA', 'Custodial UGMA'), ('Other', 'Other')]
    DETAILED_TYPES = RETIREMENT_CHOICES + BROKERAGE_CHOICES
    name = models.CharField(max_length=50, choices=DETAILED_TYPES, primary_key=True)
    category = models.CharField(max_length=20, editable=False)

    def save(self, *args, **kwargs):
        if self.name in dict(self.RETIREMENT_CHOICES):
            self.category = 'retirement'
        elif self.name in dict(self.BROKERAGE_CHOICES):
            self.category = 'brokerage'
        else:
            self.category = 'unknown'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Portfolio(models.Model):
    """
    Represents a financial portfolio.

    Attributes:
        name (str): The name of the portfolio.
        investment_platform (InvestmentPlatform): The investment platform associated with the portfolio.
        type (Type): The type of portfolio.
        detail (Detail): The detail of portfolio.
        created_at (datetime): The date and time when the portfolio was created.
    """

    name = models.CharField(max_length=100)
    investment_platform = models.ForeignKey(InvestmentPlatform, on_delete=models.PROTECT)
    brokerage_account_type = models.ForeignKey(BrokerageAccountType, null=True, on_delete=models.SET_NULL)
    category = models.CharField(max_length=20, editable=False, default='brokerage')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.category = self.brokerage_account_type.category
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class PortfolioInvestment(models.Model):
    """
    Represents an investment within a portfolio.

    Attributes:
        portfolio (Portfolio): The portfolio that this investment belongs to.
        investment (Investment): The investment object.
        quantity (int): The quantity of the investment within the portfolio.
    """

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = (('portfolio', 'investment'),)

    def __str__(self):
        return f"{self.portfolio.name} - {self.investment.symbol}"
    

class Transaction(models.Model):
    """Represents a financial transaction related to a portfolio investment.

    Attributes:
        portfolio_investment (PortfolioInvestment): The portfolio investment associated with the transaction.
        transaction_type (str): The type of transaction (BUY or SELL).
        quantity (int): The quantity of the investment.
        price (Decimal): The price of the investment.
        transaction_date (datetime): The date and time when the transaction occurred.
    """

    transaction_choices = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('DIVIDENDS', 'Dividends'),
        ('SPLITS', 'Splits'),
        ('TRANSFER', 'Transfer')
    ]

    portfolio_investment = models.ForeignKey(PortfolioInvestment, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=transaction_choices)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField()

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} of {self.portfolio_investment.investment.symbol}"