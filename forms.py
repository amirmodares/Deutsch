from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email
from flask_ckeditor import CKEditorField


class RegisterForm(FlaskForm):
    name = StringField("Name *", validators=[DataRequired()])
    email = StringField("Email *", validators=[DataRequired(), Email(message="Wrong Email Address")])
    password = PasswordField("Password *", validators=[DataRequired()])
    course_code = StringField("Code", render_kw={"placeholder": "For Registering as Course Manager, Fill This Field "
                                                                "With Given Code"})
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Wrong Email Address")])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class CourseForm(FlaskForm):
    language = StringField("Language", validators=[DataRequired()])
    teacher = StringField("Teacher", validators=[DataRequired()])
    level = StringField("Level", validators=[DataRequired()])
    month = StringField("Month", validators=[DataRequired()])
    year = StringField("Year", validators=[DataRequired()])
    submit = SubmitField("Add This New Course")


class SectionForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Add This New Section")


class WordForm(FlaskForm):
    name = StringField("Word", validators=[DataRequired()])
    meaning = StringField("Meaning", validators=[DataRequired()])
    gender = SelectField("Gender", choices=['', 'der', 'die', 'das'])
    description = CKEditorField("Description")
    submit = SubmitField("Add This New Word")


class EditWordForm(FlaskForm):
    name = StringField("Word", validators=[DataRequired()])
    meaning = StringField("Meaning", validators=[DataRequired()])
    gender = SelectField("Gender", choices=['', 'der', 'die', 'das'])
    description = CKEditorField("Description")
    submit = SubmitField("Edit This Word")


class SearchForm(FlaskForm):
    word = StringField("Search Bar", validators=[DataRequired()])
    submit = SubmitField("Search This Word")