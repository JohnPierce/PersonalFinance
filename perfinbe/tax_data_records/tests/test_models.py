# tax_data_records/tests/test_models.py

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from personal_finance_portfolio.models import (
    Portfolio, Investment, PortfolioInvestment, Transaction,
    InvestmentPlatform, BrokerageAccountType
)
from tax_data_records.models import (
    TaxableAccount, TaxLot, TaxLotDisposition,
    WashSale, TaxableEvent, Form1099B
)
from tax_data_records.services.wash_sale import WashSaleDetector

class TaxableAccountTests(TestCase):
    def setUp(self):
        # Create base objects needed for testing
        self.platform = InvestmentPlatform.objects.create(
            name='Fidelity'
        )
        self.account_type = BrokerageAccountType.objects.create(
            name='Taxable'
        )
        self.portfolio = Portfolio.objects.create(
            name='Test Portfolio',
            investment_platform=self.platform,
            brokerage_account_type=self.account_type
        )
        
    def test_taxable_account_creation(self):
        account = TaxableAccount.objects.create(
            portfolio=self.portfolio,
            cost_basis_method='FIFO'
        )
        self.assertEqual(str(account), f"Tax Settings for {self.portfolio.name}")
        self.assertTrue(account.wash_sale_tracking)
        self.assertEqual(account.cost_basis_method, 'FIFO')

class TaxLotTests(TestCase):
    def setUp(self):
        # Create necessary related objects
        self.platform = InvestmentPlatform.objects.create(name='Fidelity')
        self.account_type = BrokerageAccountType.objects.create(name='Taxable')
        self.portfolio = Portfolio.objects.create(
            name='Test Portfolio',
            investment_platform=self.platform,
            brokerage_account_type=self.account_type
        )
        self.taxable_account = TaxableAccount.objects.create(
            portfolio=self.portfolio,
            cost_basis_method='FIFO'
        )
        self.investment = Investment.objects.create(
            ticker_symbol='AAPL',
            name='Apple Inc.',
            price=Decimal('150.00')
        )
        self.portfolio_investment = PortfolioInvestment.objects.create(
            portfolio=self.portfolio,
            investment=self.investment,
            quantity=100
        )
        
    def test_tax_lot_creation(self):
        transaction = Transaction.objects.create(
            portfolio_investment=self.portfolio_investment,
            transaction_type='BUY',
            quantity=10,
            price=Decimal('150.00'),
            transaction_date=timezone.now()
        )
        
        tax_lot = TaxLot.objects.create(
            account=self.taxable_account,
            transaction=transaction,
            quantity=10,
            acquisition_date=timezone.now(),
            cost_basis=Decimal('1500.00'),
            remaining_quantity=10,
            adjusted_basis=Decimal('1500.00')
        )
        
        self.assertEqual(tax_lot.remaining_quantity, 10)
        self.assertEqual(tax_lot.adjusted_basis, Decimal('1500.00'))

class TaxLotDispositionTests(TestCase):
    def setUp(self):
        # Set up base test data
        self.setup_test_data()
        
    def setup_test_data(self):
        # Create platform and portfolio
        self.platform = InvestmentPlatform.objects.create(name='Fidelity')
        self.account_type = BrokerageAccountType.objects.create(name='Taxable')
        self.portfolio = Portfolio.objects.create(
            name='Test Portfolio',
            investment_platform=self.platform,
            brokerage_account_type=self.account_type
        )
        self.taxable_account = TaxableAccount.objects.create(
            portfolio=self.portfolio
        )
        
        # Create investment and portfolio investment
        self.investment = Investment.objects.create(
            ticker_symbol='AAPL',
            name='Apple Inc.',
            price=Decimal('150.00')
        )
        self.portfolio_investment = PortfolioInvestment.objects.create(
            portfolio=self.portfolio,
            investment=self.investment,
            quantity=100
        )
        
        # Create purchase transaction and tax lot
        self.purchase_transaction = Transaction.objects.create(
            portfolio_investment=self.portfolio_investment,
            transaction_type='BUY',
            quantity=10,
            price=Decimal('150.00'),
            transaction_date=timezone.now() - timedelta(days=400)
        )
        
        self.tax_lot = TaxLot.objects.create(
            account=self.taxable_account,
            transaction=self.purchase_transaction,
            quantity=10,
            acquisition_date=self.purchase_transaction.transaction_date,
            cost_basis=Decimal('1500.00'),
            remaining_quantity=10,
            adjusted_basis=Decimal('1500.00')
        )
        
    def test_disposition_holding_period(self):
        # Create sale transaction
        sale_transaction = Transaction.objects.create(
            portfolio_investment=self.portfolio_investment,
            transaction_type='SELL',
            quantity=5,
            price=Decimal('160.00'),
            transaction_date=timezone.now()
        )
        
        disposition = TaxLotDisposition.objects.create(
            tax_lot=self.tax_lot,
            sale_transaction=sale_transaction,
            quantity=5,
            proceeds=Decimal('800.00'),
            date=timezone.now()
        )
        
        # Test holding period calculation
        self.assertTrue(disposition.is_long_term())
        self.assertTrue(disposition.holding_period > timedelta(days=365))

class WashSaleTests(TestCase):
    def setUp(self):
        # Create platform and portfolio
        self.platform = InvestmentPlatform.objects.create(name='Fidelity')
        self.account_type = BrokerageAccountType.objects.create(name='Taxable')
        self.portfolio = Portfolio.objects.create(
            name='Test Portfolio',
            investment_platform=self.platform,
            brokerage_account_type=self.account_type
        )
        self.taxable_account = TaxableAccount.objects.create(
            portfolio=self.portfolio
        )
        
        # Create investment and portfolio investment
        self.investment = Investment.objects.create(
            ticker_symbol='AAPL',
            name='Apple Inc.',
            price=Decimal('150.00')
        )
        self.portfolio_investment = PortfolioInvestment.objects.create(
            portfolio=self.portfolio,
            investment=self.investment,
            quantity=100
        )
        
        # Create initial purchase transaction and tax lot
        self.purchase_transaction = Transaction.objects.create(
            portfolio_investment=self.portfolio_investment,
            transaction_type='BUY',
            quantity=10,
            price=Decimal('150.00'),
            transaction_date=timezone.now() - timedelta(days=400)
        )
        
        self.tax_lot = TaxLot.objects.create(
            account=self.taxable_account,
            transaction=self.purchase_transaction,
            quantity=10,
            acquisition_date=self.purchase_transaction.transaction_date,
            cost_basis=Decimal('1500.00'),
            remaining_quantity=10,
            adjusted_basis=Decimal('1500.00')
        )
        
        # Add specific wash sale test data
        self.sale_price = Decimal('140.00')  # Lower than purchase for a loss
        self.sale_transaction = Transaction.objects.create(
            portfolio_investment=self.portfolio_investment,
            transaction_type='SELL',
            quantity=10,
            price=self.sale_price,
            transaction_date=timezone.now()
        )
        
    def test_wash_sale_detection(self):
        # Create a disposition at a loss
        disposition = TaxLotDisposition.objects.create(
            tax_lot=self.tax_lot,
            sale_transaction=self.sale_transaction,
            quantity=10,
            proceeds=self.sale_price * 10,
            date=timezone.now()
        )
        
        # Create a replacement purchase within 30 days
        replacement_transaction = Transaction.objects.create(
            portfolio_investment=self.portfolio_investment,
            transaction_type='BUY',
            quantity=10,
            price=Decimal('145.00'),
            transaction_date=timezone.now() + timedelta(days=15)
        )
        
        replacement_lot = TaxLot.objects.create(
            account=self.taxable_account,
            transaction=replacement_transaction,
            quantity=10,
            acquisition_date=replacement_transaction.transaction_date,
            cost_basis=Decimal('1450.00'),
            remaining_quantity=10,
            adjusted_basis=Decimal('1450.00')
        )
        
        # Test wash sale detection
        detector = WashSaleDetector(self.taxable_account)
        detector.process_disposition(disposition)
        
        # Verify wash sale was created
        wash_sale = WashSale.objects.filter(disposition=disposition).first()
        self.assertIsNotNone(wash_sale)
        
        # Debug information
        print(f"\nTest calculations:")
        print(f"Original cost basis: {self.tax_lot.cost_basis}")
        print(f"Original quantity: {self.tax_lot.quantity}")
        print(f"Cost basis per share: {self.tax_lot.cost_basis / self.tax_lot.quantity}")
        print(f"Sale price per share: {self.sale_price}")
        print(f"Shares sold: {disposition.quantity}")
        
        # Calculate expected loss
        cost_basis_per_share = self.tax_lot.cost_basis / self.tax_lot.quantity
        loss_per_share = cost_basis_per_share - self.sale_price
        expected_loss = loss_per_share * disposition.quantity
        
        print(f"Loss per share: {loss_per_share}")
        print(f"Expected total loss: {expected_loss}")
        print(f"Actual wash sale disallowed loss: {wash_sale.disallowed_loss}\n")
        
        self.assertEqual(
            wash_sale.disallowed_loss,
            abs(expected_loss),
            f"Expected disallowed loss of {abs(expected_loss)}, got {wash_sale.disallowed_loss}"
        )

class Form1099BTests(TestCase):
    def setUp(self):
        # Create platform and portfolio
        self.platform = InvestmentPlatform.objects.create(name='Fidelity')
        self.account_type = BrokerageAccountType.objects.create(name='Taxable')
        self.portfolio = Portfolio.objects.create(
            name='Test Portfolio',
            investment_platform=self.platform,
            brokerage_account_type=self.account_type
        )
        self.taxable_account = TaxableAccount.objects.create(
            portfolio=self.portfolio
        )
        
        # Create investment and portfolio investment
        self.investment = Investment.objects.create(
            ticker_symbol='AAPL',
            name='Apple Inc.',
            price=Decimal('150.00')
        )
        self.portfolio_investment = PortfolioInvestment.objects.create(
            portfolio=self.portfolio,
            investment=self.investment,
            quantity=100
        )
        
    def test_form_calculation(self):
        form = Form1099B.objects.create(
            account=self.taxable_account,
            tax_year=2024
        )
        
        # Add some test dispositions
        form.dispositions.add(self.create_test_disposition(
            is_long_term=True,
            proceeds=Decimal('1000.00'),
            cost_basis=Decimal('800.00')
        ))
        
        form.dispositions.add(self.create_test_disposition(
            is_long_term=False,
            proceeds=Decimal('500.00'),
            cost_basis=Decimal('600.00')
        ))
        
        form.calculate_totals()
        
        self.assertEqual(form.lt_covered_proceeds, Decimal('1000.00'))
        self.assertEqual(form.lt_covered_basis, Decimal('800.00'))
        self.assertEqual(form.st_covered_proceeds, Decimal('500.00'))
        self.assertEqual(form.st_covered_basis, Decimal('600.00'))

    def create_test_disposition(self, is_long_term, proceeds, cost_basis):
        # Helper method to create test dispositions
        acquisition_date = timezone.now() - timedelta(
            days=400 if is_long_term else 100
        )
        
        transaction = Transaction.objects.create(
            portfolio_investment=self.portfolio_investment,
            transaction_type='SELL',
            quantity=10,
            price=proceeds / 10,
            transaction_date=timezone.now()
        )
        
        tax_lot = TaxLot.objects.create(
            account=self.taxable_account,
            transaction=transaction,
            quantity=10,
            acquisition_date=acquisition_date,
            cost_basis=cost_basis,
            remaining_quantity=0,
            adjusted_basis=cost_basis / 10
        )
        
        return TaxLotDisposition.objects.create(
            tax_lot=tax_lot,
            sale_transaction=transaction,
            quantity=10,
            proceeds=proceeds,
            date=timezone.now()
        )

# Add to tax_data_records/tests/__init__.py to make the test module discoverable