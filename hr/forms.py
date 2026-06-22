from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from backoffice.models import BackOffice
from branch.models import Branch, BranchManager
from finance.models import Finance
from followup.models import FollowUp
from marketing.models import Marketing
from staff.models import Staff
from core.countries import COUNTRY_NAMES
from core.models import UserProfile
from hr.models import Hr
from hr.team_documents import TeamDocumentFormMixin, add_document_fields, team_branch_field

FORM_CONTROL = {"class": "form-control"}

SALARY_INPUT = {
    **FORM_CONTROL,
    "step": "0.01",
    "min": "0",
    "placeholder": "0.00",
}

SALARY_PART_INPUT = {
    **SALARY_INPUT,
    "oninput": "recalcStaffTotal(this)",
    "onkeyup": "recalcStaffTotal(this)",
    "onchange": "recalcStaffTotal(this)",
}


class HRRegistrationForm(forms.Form):
    """Fields match Hr model + password for login."""

    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Phone",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+91 98765 43210"}),
    )
    join_date = forms.DateField(
        label="Join date",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password (min 4 characters)"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm password"}),
    )
    profile_picture = forms.ImageField(
        label="Profile picture",
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )

    def clean_username(self):
        name = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=name).exists():
            raise forms.ValidationError("This username is already taken.")
        return name

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        if p1 and len(p1) < 4:
            raise forms.ValidationError("Password must be at least 4 characters.")
        return cleaned

    def save(self):
        account = User(
            username=self.cleaned_data["username"],
            is_active=True,
        )
        account.password = make_password(self.cleaned_data["password1"])
        account.save()

        profile = UserProfile.objects.create(
            user=account,
            user_type=UserProfile.UserType.HR,
            phone=self.cleaned_data["phone"],
        )
        if self.cleaned_data.get("profile_picture"):
            profile.profile_picture = self.cleaned_data["profile_picture"]
            profile.save(update_fields=["profile_picture", "updated_at"])
        Hr.objects.create(
            username=account,
            phone=self.cleaned_data["phone"],
            join_date=self.cleaned_data["join_date"],
            date_of_birth=self.cleaned_data["date_of_birth"],
        )
        return account


class BranchForm(forms.ModelForm):
    nationality = forms.CharField(
        label="Nationality",
        widget=forms.TextInput(
            attrs={
                **FORM_CONTROL,
                "list": "branch-country-list",
                "autocomplete": "off",
                "placeholder": "Search country…",
            }
        ),
    )

    class Meta:
        model = Branch
        fields = (
            "name",
            "email",
            "phone",
            "opening_date",
            "nationality",
            "address",
            "city",
            "state",
        )
        widgets = {
            "name": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "Branch name"}),
            "email": forms.EmailInput(attrs={**FORM_CONTROL, "placeholder": "branch@company.com"}),
            "phone": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "+91 98765 43210"}),
            "opening_date": forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
            "address": forms.Textarea(attrs={**FORM_CONTROL, "rows": 2, "placeholder": "Street address"}),
            "city": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "City"}),
            "state": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "State"}),
        }

    def clean_nationality(self):
        value = (self.cleaned_data.get("nationality") or "").strip()
        if not value:
            raise forms.ValidationError("This field is required.")
        if value not in COUNTRY_NAMES:
            raise forms.ValidationError("Please select a valid country from the list.")
        return value


class BranchManagerForm(TeamDocumentFormMixin, forms.Form):
    """Create a branch manager login linked to a branch."""

    branch = team_branch_field(required=False)
    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "Username"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Mobile number",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "+91 98765 43210"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={**FORM_CONTROL, "placeholder": "manager@company.com"}),
    )
    join_date = forms.DateField(
        label="Join date",
        widget=forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={**FORM_CONTROL, "placeholder": "Password (min 4 characters)"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={**FORM_CONTROL, "placeholder": "Confirm password"}),
    )
    profile_picture = forms.ImageField(
        label="Profile picture",
        required=False,
        widget=forms.FileInput(attrs={**FORM_CONTROL, "accept": "image/*"}),
    )

    def __init__(self, *args, branch_required=False, hide_branch=False, **kwargs):
        super().__init__(*args, **kwargs)
        if hide_branch:
            del self.fields["branch"]
        elif branch_required:
            self.fields["branch"].required = True

    def clean_username(self):
        name = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=name).exists():
            raise forms.ValidationError("This username is already taken.")
        return name

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        if p1 and len(p1) < 4:
            raise forms.ValidationError("Password must be at least 4 characters.")
        if "branch" in self.fields and not cleaned.get("branch"):
            raise forms.ValidationError("Please select a branch.")
        return cleaned

    def save(self, branch=None):
        branch = branch or self.cleaned_data.get("branch")
        account = User(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            is_active=True,
        )
        account.password = make_password(self.cleaned_data["password1"])
        account.save()

        profile = UserProfile.objects.create(
            user=account,
            user_type=UserProfile.UserType.BRANCH,
            phone=self.cleaned_data["phone"],
        )
        if self.cleaned_data.get("profile_picture"):
            profile.profile_picture = self.cleaned_data["profile_picture"]
            profile.save(update_fields=["profile_picture", "updated_at"])
        manager = BranchManager.objects.create(
            user=account,
            branch=branch,
            phone=self.cleaned_data["phone"],
            join_date=self.cleaned_data["join_date"],
        )
        self.save_team_documents(account, branch=branch)
        return manager


add_document_fields(BranchManagerForm)


class TeamProfileForm(TeamDocumentFormMixin, forms.Form):
    """Shared fields for staff, follow-up, and back office team profiles."""

    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "Username"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Mobile number",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "+91 98765 43210"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={**FORM_CONTROL, "placeholder": "user@company.com"}),
    )
    join_date = forms.DateField(
        label="Join date",
        widget=forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
    )
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={**FORM_CONTROL, "placeholder": "Password (min 4 characters)"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={**FORM_CONTROL, "placeholder": "Confirm password"}),
    )
    profile_picture = forms.ImageField(
        label="Profile picture",
        required=False,
        widget=forms.FileInput(attrs={**FORM_CONTROL, "accept": "image/*"}),
    )

    user_type = None
    profile_model = None

    def __init__(self, *args, email_placeholder="user@company.com", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["placeholder"] = email_placeholder

    def clean_username(self):
        name = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=name).exists():
            raise forms.ValidationError("This username is already taken.")
        return name

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        if p1 and len(p1) < 4:
            raise forms.ValidationError("Password must be at least 4 characters.")
        return cleaned

    def save(self):
        if not self.user_type or not self.profile_model:
            raise NotImplementedError("Subclass must set user_type and profile_model.")

        account = User(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            is_active=True,
        )
        account.password = make_password(self.cleaned_data["password1"])
        account.save()

        profile = UserProfile.objects.create(
            user=account,
            user_type=self.user_type,
            phone=self.cleaned_data["phone"],
        )
        if self.cleaned_data.get("profile_picture"):
            profile.profile_picture = self.cleaned_data["profile_picture"]
            profile.save(update_fields=["profile_picture", "updated_at"])

        member = self.profile_model.objects.create(
            user=account,
            phone=self.cleaned_data["phone"],
            join_date=self.cleaned_data["join_date"],
            date_of_birth=self.cleaned_data["date_of_birth"],
        )
        self.save_team_documents(account)
        return member


add_document_fields(TeamProfileForm)


class StaffForm(TeamProfileForm):
    user_type = UserProfile.UserType.STAFF
    profile_model = Staff
    branch = team_branch_field(required=True)
    basic_salary = forms.DecimalField(
        label="Basic salary",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={**SALARY_PART_INPUT}),
    )
    other_salary = forms.DecimalField(
        label="Other salary",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={**SALARY_PART_INPUT}),
    )
    total_salary = forms.DecimalField(
        label="Total salary",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={**SALARY_INPUT, "readonly": "readonly"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, email_placeholder="staff@company.com", **kwargs)

    def save(self):
        member = super().save()
        member.branch = self.cleaned_data["branch"]
        member.basic_salary = self.cleaned_data["basic_salary"]
        member.other_salary = self.cleaned_data["other_salary"]
        member.total_salary = self.cleaned_data["total_salary"]
        member.save(
            update_fields=[
                "branch",
                "basic_salary",
                "other_salary",
                "total_salary",
                "updated_at",
            ]
        )
        return member


class FollowUpForm(TeamProfileForm):
    user_type = UserProfile.UserType.FOLLOWUP
    profile_model = FollowUp
    branch = team_branch_field(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, email_placeholder="followup@company.com", **kwargs)

    def save(self):
        member = super().save()
        member.branch = self.cleaned_data["branch"]
        member.save(update_fields=["branch", "updated_at"])
        return member


class BackOfficeForm(TeamProfileForm):
    user_type = UserProfile.UserType.BACKOFFICE
    profile_model = BackOffice
    branch = team_branch_field(required=True)
    is_backoffice_head = forms.BooleanField(
        required=False,
        label="Back office head",
        help_text="Head can approve/reject leads and see all back office team data.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, email_placeholder="backoffice@company.com", **kwargs)

    def save(self):
        member = super().save()
        member.branch = self.cleaned_data["branch"]
        member.is_backoffice_head = self.cleaned_data.get("is_backoffice_head", False)
        member.save(update_fields=["branch", "is_backoffice_head", "updated_at"])
        return member


class FinanceForm(TeamProfileForm):
    user_type = UserProfile.UserType.FINANCE
    profile_model = Finance
    branch = team_branch_field(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, email_placeholder="finance@company.com", **kwargs)

    def save(self):
        member = super().save()
        member.branch = self.cleaned_data["branch"]
        member.save(update_fields=["branch", "updated_at"])
        return member


class MarketingForm(TeamProfileForm):
    user_type = UserProfile.UserType.MARKETING
    profile_model = Marketing
    branch = team_branch_field(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, email_placeholder="marketing@company.com", **kwargs)

    def save(self):
        member = super().save()
        member.branch = self.cleaned_data["branch"]
        member.save(update_fields=["branch", "updated_at"])
        return member


class TeamProfileEditForm(forms.Form):
    """Update staff, follow-up, or back office (username cannot change)."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={**FORM_CONTROL, "placeholder": "user@company.com"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Mobile number",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "+91 98765 43210"}),
    )
    join_date = forms.DateField(
        label="Join date",
        widget=forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
    )
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
    )
    branch = team_branch_field(required=True)
    password1 = forms.CharField(
        label="New password",
        required=False,
        widget=forms.PasswordInput(
            attrs={**FORM_CONTROL, "placeholder": "Leave blank to keep current password", "autocomplete": "new-password"}
        ),
    )
    password2 = forms.CharField(
        label="Confirm new password",
        required=False,
        widget=forms.PasswordInput(attrs={**FORM_CONTROL, "placeholder": "Confirm new password", "autocomplete": "new-password"}),
    )
    profile_picture = forms.ImageField(
        label="Profile picture",
        required=False,
        widget=forms.FileInput(attrs={**FORM_CONTROL, "accept": "image/*"}),
    )

    def __init__(self, member, *args, **kwargs):
        self.member = member
        user = member.user
        initial = {
            "email": user.email,
            "phone": member.phone,
            "join_date": member.join_date,
            "date_of_birth": member.date_of_birth,
            "branch": member.branch_id,
        }
        super().__init__(*args, initial=initial, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exclude(pk=self.member.user_id).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords do not match.")
            if len(p1) < 4:
                raise forms.ValidationError("Password must be at least 4 characters.")
        return cleaned

    def save(self):
        user = self.member.user
        user.email = self.cleaned_data["email"]
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        user.save()

        profile = getattr(user, "profile", None)
        if profile:
            profile.phone = self.cleaned_data["phone"]
            if self.cleaned_data.get("profile_picture"):
                profile.profile_picture = self.cleaned_data["profile_picture"]
            profile.save()

        self.member.phone = self.cleaned_data["phone"]
        self.member.join_date = self.cleaned_data["join_date"]
        self.member.date_of_birth = self.cleaned_data["date_of_birth"]
        self.member.branch = self.cleaned_data["branch"]
        self.member.save()
        return self.member


class BackOfficeProfileEditForm(TeamProfileEditForm):
    is_backoffice_head = forms.BooleanField(
        required=False,
        label="Back office head",
        help_text="Head can approve/reject leads and see all back office team data.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, member, *args, **kwargs):
        super().__init__(member, *args, **kwargs)
        self.fields["is_backoffice_head"].initial = member.is_backoffice_head

    def save(self):
        member = super().save()
        member.is_backoffice_head = self.cleaned_data.get("is_backoffice_head", False)
        member.save(update_fields=["is_backoffice_head", "updated_at"])
        return member


class StaffProfileEditForm(TeamProfileEditForm):
    basic_salary = forms.DecimalField(
        label="Basic salary",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={**SALARY_PART_INPUT}),
    )
    other_salary = forms.DecimalField(
        label="Other salary",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={**SALARY_PART_INPUT}),
    )
    total_salary = forms.DecimalField(
        label="Total salary",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={**SALARY_INPUT, "readonly": "readonly"}),
    )

    def __init__(self, member, *args, **kwargs):
        super().__init__(member, *args, **kwargs)
        self.fields["basic_salary"].initial = member.basic_salary
        self.fields["other_salary"].initial = member.other_salary
        self.fields["total_salary"].initial = member.total_salary

    def save(self):
        member = super().save()
        member.basic_salary = self.cleaned_data["basic_salary"]
        member.other_salary = self.cleaned_data["other_salary"]
        member.total_salary = self.cleaned_data["total_salary"]
        member.save(
            update_fields=[
                "basic_salary",
                "other_salary",
                "total_salary",
                "updated_at",
            ]
        )
        return member


class OrgTeamProfileEditForm(forms.Form):
    """Update finance or marketing profiles (no branch assignment)."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={**FORM_CONTROL, "placeholder": "user@company.com"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Mobile number",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "+91 98765 43210"}),
    )
    join_date = forms.DateField(
        label="Join date",
        widget=forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
    )
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
    )
    password1 = forms.CharField(
        label="New password",
        required=False,
        widget=forms.PasswordInput(
            attrs={**FORM_CONTROL, "placeholder": "Leave blank to keep current password", "autocomplete": "new-password"}
        ),
    )
    password2 = forms.CharField(
        label="Confirm new password",
        required=False,
        widget=forms.PasswordInput(attrs={**FORM_CONTROL, "placeholder": "Confirm new password", "autocomplete": "new-password"}),
    )
    profile_picture = forms.ImageField(
        label="Profile picture",
        required=False,
        widget=forms.FileInput(attrs={**FORM_CONTROL, "accept": "image/*"}),
    )

    def __init__(self, member, *args, **kwargs):
        self.member = member
        user = member.user
        initial = {
            "email": user.email,
            "phone": member.phone,
            "join_date": member.join_date,
            "date_of_birth": member.date_of_birth,
        }
        super().__init__(*args, initial=initial, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exclude(pk=self.member.user_id).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords do not match.")
            if len(p1) < 4:
                raise forms.ValidationError("Password must be at least 4 characters.")
        return cleaned

    def save(self):
        user = self.member.user
        user.email = self.cleaned_data["email"]
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        user.save()

        profile = getattr(user, "profile", None)
        if profile:
            profile.phone = self.cleaned_data["phone"]
            if self.cleaned_data.get("profile_picture"):
                profile.profile_picture = self.cleaned_data["profile_picture"]
            profile.save()

        self.member.phone = self.cleaned_data["phone"]
        self.member.join_date = self.cleaned_data["join_date"]
        self.member.date_of_birth = self.cleaned_data["date_of_birth"]
        self.member.save()
        return self.member


class BranchManagerEditForm(forms.Form):
    """Update branch manager profile (username cannot change)."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={**FORM_CONTROL, "placeholder": "manager@company.com"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Mobile number",
        widget=forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "+91 98765 43210"}),
    )
    join_date = forms.DateField(
        label="Join date",
        widget=forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
    )
    branch = team_branch_field(required=True)
    password1 = forms.CharField(
        label="New password",
        required=False,
        widget=forms.PasswordInput(
            attrs={**FORM_CONTROL, "placeholder": "Leave blank to keep current password", "autocomplete": "new-password"}
        ),
    )
    password2 = forms.CharField(
        label="Confirm new password",
        required=False,
        widget=forms.PasswordInput(attrs={**FORM_CONTROL, "placeholder": "Confirm new password", "autocomplete": "new-password"}),
    )
    profile_picture = forms.ImageField(
        label="Profile picture",
        required=False,
        widget=forms.FileInput(attrs={**FORM_CONTROL, "accept": "image/*"}),
    )

    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        user = manager.user
        initial = {
            "email": user.email,
            "phone": manager.phone,
            "join_date": manager.join_date,
            "branch": manager.branch_id,
        }
        super().__init__(*args, initial=initial, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exclude(pk=self.manager.user_id).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords do not match.")
            if len(p1) < 4:
                raise forms.ValidationError("Password must be at least 4 characters.")
        return cleaned

    def save(self):
        user = self.manager.user
        user.email = self.cleaned_data["email"]
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        user.save()

        profile = getattr(user, "profile", None)
        if profile:
            profile.phone = self.cleaned_data["phone"]
            if self.cleaned_data.get("profile_picture"):
                profile.profile_picture = self.cleaned_data["profile_picture"]
            profile.save()

        self.manager.phone = self.cleaned_data["phone"]
        self.manager.join_date = self.cleaned_data["join_date"]
        self.manager.branch = self.cleaned_data["branch"]
        self.manager.save()
        return self.manager
