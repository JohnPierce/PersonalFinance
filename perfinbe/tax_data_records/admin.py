# tax_data_records/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    TaxableAccount,
    TaxLot,
    TaxLotDisposition,
    WashSale,
    TaxableEvent,
    Form1099B
)

@admin.register(TaxableAccount)
class TaxableAccountAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'cost_basis_method', 'wash_sale_tracking')
    list_filter = ('cost_basis_method', 'wash_sale_tracking')
    search_fields = ('portfolio__name',)

@admin.register(TaxLot)
class TaxLotAdmin(admin.ModelAdmin):
    list_display = (
        'get_symbol',
        'get_portfolio',
        'quantity',
        'remaining_quantity',
        'acquisition_date',
        'cost_basis',
        'adjusted_basis'
    )
    list_filter = (
        'account__portfolio__name',
        'acquisition_date',
    )
    search_fields = (
        'account__portfolio__name',
        'transaction__portfolio_investment__investment__ticker_symbol',
    )
    readonly_fields = ('adjusted_basis',)

    def get_symbol(self, obj):
        return obj.transaction.portfolio_investment.investment.ticker_symbol
    get_symbol.short_description = 'Symbol'
    get_symbol.admin_order_field = 'transaction__portfolio_investment__investment__ticker_symbol'

    def get_portfolio(self, obj):
        return obj.account.portfolio.name
    get_portfolio.short_description = 'Portfolio'
    get_portfolio.admin_order_field = 'account__portfolio__name'

@admin.register(TaxLotDisposition)
class TaxLotDispositionAdmin(admin.ModelAdmin):
    list_display = (
        'get_symbol',
        'quantity',
        'proceeds',
        'date',
        'get_holding_period_status',
        'view_wash_sales'
    )
    list_filter = (
        'date',
        'tax_lot__account__portfolio__name',
    )
    search_fields = (
        'tax_lot__transaction__portfolio_investment__investment__ticker_symbol',
        'tax_lot__account__portfolio__name',
    )

    def get_symbol(self, obj):
        return obj.tax_lot.transaction.portfolio_investment.investment.ticker_symbol
    get_symbol.short_description = 'Symbol'

    def get_holding_period_status(self, obj):
        return 'Long Term' if obj.is_long_term() else 'Short Term'
    get_holding_period_status.short_description = 'Holding Period'

    def view_wash_sales(self, obj):
        count = obj.wash_sales.count()
        if count:
            url = reverse('admin:tax_data_records_washsale_changelist') + f'?disposition__id={obj.id}'
            return format_html('<a href="{}">View {} Wash Sale{}</a>', 
                             url, count, 's' if count != 1 else '')
        return 'No wash sales'
    view_wash_sales.short_description = 'Wash Sales'

@admin.register(WashSale)
class WashSaleAdmin(admin.ModelAdmin):
    list_display = (
        'get_symbol',
        'get_disposition_date',
        'get_replacement_date',
        'disallowed_loss'
    )
    list_filter = (
        'disposition__date',
        'replacement_lot__acquisition_date',
    )
    search_fields = (
        'disposition__tax_lot__transaction__portfolio_investment__investment__ticker_symbol',
    )

    def get_symbol(self, obj):
        return obj.disposition.tax_lot.transaction.portfolio_investment.investment.ticker_symbol
    get_symbol.short_description = 'Symbol'

    def get_disposition_date(self, obj):
        return obj.disposition.date
    get_disposition_date.short_description = 'Disposition Date'
    get_disposition_date.admin_order_field = 'disposition__date'

    def get_replacement_date(self, obj):
        return obj.replacement_lot.acquisition_date
    get_replacement_date.short_description = 'Replacement Date'
    get_replacement_date.admin_order_field = 'replacement_lot__acquisition_date'

@admin.register(TaxableEvent)
class TaxableEventAdmin(admin.ModelAdmin):
    list_display = (
        'get_symbol',
        'event_type',
        'amount',
        'date',
        'get_portfolio'
    )
    list_filter = (
        'event_type',
        'date',
        'account__portfolio__name'
    )
    search_fields = (
        'transaction__portfolio_investment__investment__ticker_symbol',
        'account__portfolio__name'
    )

    def get_symbol(self, obj):
        return obj.transaction.portfolio_investment.investment.ticker_symbol
    get_symbol.short_description = 'Symbol'

    def get_portfolio(self, obj):
        return obj.account.portfolio.name
    get_portfolio.short_description = 'Portfolio'

@admin.register(Form1099B)
class Form1099BAdmin(admin.ModelAdmin):
    list_display = (
        'account',
        'tax_year',
        'st_covered_proceeds',
        'st_covered_basis',
        'lt_covered_proceeds',
        'lt_covered_basis',
        'wash_sale_adjustments'
    )
    list_filter = ('tax_year', 'account__portfolio__name')
    search_fields = ('account__portfolio__name',)
    
    readonly_fields = (
        'st_covered_proceeds',
        'st_covered_basis',
        'lt_covered_proceeds',
        'lt_covered_basis',
        'wash_sale_adjustments'
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()  # Recalculate totals after saving