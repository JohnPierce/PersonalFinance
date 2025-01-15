# tax_data_records/services/wash_sale.py

from datetime import timedelta
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from ..models import TaxLot, WashSale

class WashSaleDetector:
    """
    Service class to detect and record wash sales when dispositions occur at a loss
    and replacement securities are purchased within the wash sale window.
    """
    
    def __init__(self, taxable_account):
        self.account = taxable_account
    
    def process_disposition(self, disposition):
        """
        Check for wash sales when a new disposition occurs.
        
        Args:
            disposition (TaxLotDisposition): The new disposition to check
        """
        if not self.account.wash_sale_tracking:
            return
            
        # Calculate realized loss
        cost_basis_per_share = disposition.tax_lot.cost_basis / disposition.tax_lot.quantity
        sale_price_per_share = disposition.proceeds / disposition.quantity
        realized_loss = (cost_basis_per_share - sale_price_per_share) * disposition.quantity
        
        # Only process if there's a loss
        if realized_loss <= 0:
            return
            
        # Define wash sale window
        window_start = disposition.date - timedelta(days=30)
        window_end = disposition.date + timedelta(days=30)
        
        # Find potential replacement lots
        replacement_lots = TaxLot.objects.filter(
            account=self.account,
            transaction__portfolio_investment__investment=
                disposition.sale_transaction.portfolio_investment.investment,
            acquisition_date__gte=window_start,
            acquisition_date__lte=window_end
        ).exclude(
            transaction=disposition.tax_lot.transaction
        )
        
        # Process each potential replacement lot
        for replacement_lot in replacement_lots:
            # Create wash sale record
            wash_sale = WashSale.objects.create(
                disposition=disposition,
                replacement_lot=replacement_lot,
                disallowed_loss=realized_loss,  # This is already positive
                wash_sale_window_start=window_start,
                wash_sale_window_end=window_end
            )
            
            # Adjust replacement lot's basis
            replacement_lot.adjusted_basis = (
                replacement_lot.adjusted_basis + 
                (realized_loss / replacement_lot.quantity)
            )
            replacement_lot.save()
    
    def detect_wash_sales_for_period(self, start_date, end_date):
        """
        Retroactively check for wash sales in a given period.
        
        Args:
            start_date (datetime): Start of period to check
            end_date (datetime): End of period to check
        """
        dispositions = TaxLotDisposition.objects.filter(
            tax_lot__account=self.account,
            date__gte=start_date,
            date__lte=end_date
        )
        
        for disposition in dispositions:
            self.process_disposition(disposition)
    
    def get_wash_sale_summary(self, tax_year):
        """
        Get summary of wash sales for a tax year.
        
        Args:
            tax_year (int): The tax year to summarize
        
        Returns:
            dict: Summary statistics about wash sales
        """
        wash_sales = WashSale.objects.filter(
            disposition__tax_lot__account=self.account,
            disposition__date__year=tax_year
        )
        
        total_disallowed = sum(ws.disallowed_loss for ws in wash_sales)
        count = wash_sales.count()
        
        return {
            'tax_year': tax_year,
            'wash_sale_count': count,
            'total_disallowed_losses': total_disallowed,
            'average_disallowed_loss': (
                total_disallowed / count if count > 0 else Decimal('0')
            )
        }