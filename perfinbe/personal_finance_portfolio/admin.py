from django.contrib import admin

# Register your models here.
# personal_finance_portfolio/admin.py

from .models import Investment, InvestmentCategory, Category, InvestmentPlatform, Portfolio, PortfolioInvestment, Transaction, BrokerageAccountType
#from .models import Stock, ETF, MutualFund, Bond

class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'ticker_symbol', 'price', 'last_updated')
    list_filter = ('name',)
    search_fields = ('name', 'ticker_symbol')
    ordering = ('ticker_symbol',)

class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'investment_platform', 'category')
    list_filter = ('category', 'investment_platform')
    search_fields = ('name', 'investment_platform', 'category')
    ordering = ('name',)

admin.site.register(Investment, InvestmentAdmin)
admin.site.register(InvestmentCategory)
#admin.site.register(Stock)
#admin.site.register(ETF)
#admin.site.register(MutualFund)
#admin.site.register(Bond)
admin.site.register(Category)
admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(PortfolioInvestment)
admin.site.register(Transaction)
admin.site.register(BrokerageAccountType)
admin.site.register(InvestmentPlatform)
