from django.shortcuts import render

# Create your views here.
# personal_finance_portfolio/views.py

from .models import Portfolio, Investment, PortfolioInvestment, Transaction

def portfolio_list(request):
    portfolios = Portfolio.objects.all()
    return render(request, 'portfolio_list.html', {'portfolios': portfolios})
