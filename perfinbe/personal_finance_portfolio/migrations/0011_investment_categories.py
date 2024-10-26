# Generated by Django 5.0.6 on 2024-07-28 14:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("personal_finance_portfolio", "0010_remove_stock_categories"),
    ]

    operations = [
        migrations.AddField(
            model_name="investment",
            name="categories",
            field=models.ManyToManyField(
                through="personal_finance_portfolio.InvestmentCategory",
                to="personal_finance_portfolio.category",
            ),
        ),
    ]