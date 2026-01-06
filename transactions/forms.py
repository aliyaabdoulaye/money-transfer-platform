"""
Formulaires pour les transactions
"""
from django import forms
from decimal import Decimal


class DepositForm(forms.Form):
    """
    Formulaire pour effectuer un dépôt
    """
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('100'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': '10000',
            'step': '0.01'
        }),
        label='Montant (FCFA)',
        help_text='Montant minimum : 100 FCFA'
    )
    
    description = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Description optionnelle'
        }),
        label='Description'
    )


class TransferForm(forms.Form):
    """
    Formulaire pour effectuer un transfert
    """
    receiver_phone = forms.CharField(
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '+228XXXXXXXX'
        }),
        label='Numéro du destinataire',
        help_text='Format: +228XXXXXXXX'
    )
    
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('100'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '5000',
            'step': '0.01'
        }),
        label='Montant (FCFA)',
        help_text='Montant minimum : 100 FCFA'
    )
    
    description = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Description optionnelle'
        }),
        label='Description'
    )


class WithdrawalForm(forms.Form):
    """
    Formulaire pour demander un retrait (première étape)
    """
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('500'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
            'placeholder': '10000',
            'step': '0.01'
        }),
        label='Montant à retirer (FCFA)',
        help_text='Montant minimum : 500 FCFA. Des frais de 2% seront appliqués.'
    )
    
    description = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
            'placeholder': 'Description optionnelle'
        }),
        label='Description'
    )


class WithdrawalOTPForm(forms.Form):
    """
    Formulaire de vérification OTP pour le retrait (deuxième étape)
    """
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent text-center text-2xl tracking-widest',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autocomplete': 'off'
        }),
        label='Code OTP'
    )
    
    def clean_otp_code(self):
        code = self.cleaned_data.get('otp_code')
        if not code.isdigit():
            raise forms.ValidationError('Le code OTP doit contenir uniquement des chiffres.')
        return code