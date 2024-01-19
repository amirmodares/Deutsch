from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import LoginForm, WordForm, CourseForm, SectionForm, EditWordForm, RegisterForm, SearchForm
from functools import wraps
import os
import random
import string
import random


# CONNECT TO DB
app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deutsch.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()


# ----------------------------------------------- CONFIGURE TABLES ------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "user_table"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    study_course = db.Column(db.String(150), nullable=True)
    password = db.Column(db.String(250), nullable=False)
    img = db.Column(db.String(250), nullable=True)
    date_of_register = db.Column(db.String(150), nullable=False)
    has_courses = relationship("Course", back_populates="belong_to_user")
    extra = db.Column(db.String(150), nullable=True)


class Course(db.Model):
    __tablename__ = "course_table"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    language = db.Column(db.String(20), nullable=True)
    level = db.Column(db.String(20), nullable=True)
    teacher = db.Column(db.String(50), nullable=True)
    month = db.Column(db.String(20), nullable=True)
    year = db.Column(db.String(20), nullable=True)
    code = db.Column(db.String(20), nullable=True)
    date_of_creation = db.Column(db.String(50), nullable=True)
    img = db.Column(db.String(250))
    belong_to_user = relationship("User", back_populates="has_courses")
    belong_to_user_id = db.Column(db.Integer, db.ForeignKey('user_table.id'))
    has_section = relationship("Section", back_populates="belong_to_course")
    extra = db.Column(db.String(150), nullable=True)


class Section(db.Model):
    __tablename__ = "section_table"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    img = db.Column(db.String(250), nullable=True)
    belong_to_course = relationship("Course", back_populates="has_section")
    belong_to_course_id = db.Column(db.Integer, db.ForeignKey('course_table.id'))
    has_word = relationship("Word", back_populates="belong_to_section")
    extra = db.Column(db.String(150), nullable=True)


class Word(db.Model):
    __tablename__ = "word_table"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    meaning = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(20), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    img = db.Column(db.String(250), nullable=True)
    belong_to_section = relationship("Section", back_populates="has_word")
    belong_to_section_id = db.Column(db.Integer, db.ForeignKey('section_table.id'))
    extra = db.Column(db.String(150), nullable=True)

# ----------------------------------------------- Forms ------------------------------------------


# ----------------------------------------------- route controllers ------------------------------------------


@app.route('/')
def index():
    user_counter = len(db.session.query(User).all())
    word_counter = len(db.session.query(Word).all())
    course_counter = len(db.session.query(Course).all())
    user_name = ''
    if current_user.is_authenticated:
        user_name = current_user.name
    return render_template("index.html", logged_in=current_user.is_authenticated, user_name=user_name,
                           user_counter=user_counter, word_counter=word_counter, course_counter=course_counter)


@app.route('/register', methods=['POST', 'GET'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        if not User.query.filter_by(email=register_form.email.data).first():
            new_user = User()
            hashed_pass = generate_password_hash(password=register_form.password.data,
                                                 method="pbkdf2:sha256",
                                                 salt_length=8)
            new_user.name = register_form.name.data
            new_user.password = hashed_pass
            new_user.email = register_form.email.data
            new_user.date_of_register = date.today().strftime("%B %d, %Y")
            if not register_form.course_code.data:
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
            else:
                if Course.query.filter_by(code=register_form.course_code.data).first():
                    founded_course = Course.query.filter_by(code=register_form.course_code.data).first()
                    if not founded_course.belong_to_user_id:
                        db.session.add(new_user)
                        db.session.commit()
                        founded_user = User.query.filter_by(email=register_form.email.data).first()
                        founded_course.belong_to_user_id = founded_user.id
                        db.session.add(founded_course)
                        db.session.commit()
                        return redirect(url_for('login'))
                    else:
                        flash('This Course Is Belonged To Someone Else')
                        return redirect(url_for('register'))
                else:
                    flash('Entered Code is Wrong')
                    return redirect(url_for('register'))

        else:
            flash('Your Email already has been registered')
            return redirect(url_for('login'))
    return render_template("register.html", form=register_form)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        logged_in_user = User.query.filter_by(email=login_form.email.data).first()
        if logged_in_user:
            if check_password_hash(logged_in_user.password, login_form.password.data):
                login_user(logged_in_user)
                if logged_in_user.id == 1:
                    return redirect(url_for('admin'))
                elif logged_in_user.study_course or logged_in_user.has_courses:
                    return redirect(url_for('profile'))
                else:
                    return redirect(url_for('choose_course'))
            else:
                flash('The Entered Password Is Wrong')
                return redirect(url_for('login'))
        else:
            flash('The Entered Email Is Wrong')
            return redirect(url_for('login'))
    return render_template("login.html", form=login_form)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.id == 1:
                return f(*args, **kwargs)
        return abort(403)

    return decorated_function


@app.route('/admin')
@admin_only
def admin():
    all_courses = db.session.query(Course).all()
    user_name = ''
    if current_user.is_authenticated:
        user_name = current_user.name
    return render_template('admin.html', logged_in=current_user.is_authenticated, user_name=user_name,
                           all_courses=all_courses)


@app.route('/delete_course/<int:course_id>')
@admin_only
def delete_course(course_id):
    course_to_delete = Course.query.get(course_id)
    if course_to_delete.belong_to_user_id:
        flash('This Course Has Owner, It Can Not Be Deleted')
    else:
        db.session.delete(course_to_delete)
        db.session.commit()
    return redirect(url_for('admin'))


@app.route('/course_creation', methods=['POST', 'GET'])
@admin_only
def course_creation():
    user_name = current_user.name
    course_form = CourseForm()
    if course_form.validate_on_submit():
        new_course = Course()
        new_course.code = n = ''.join(random.choices(string.ascii_uppercase, k=20))
        new_course.language = course_form.language.data
        new_course.level = course_form.level.data
        new_course.teacher = course_form.teacher.data
        new_course.month = course_form.month.data
        new_course.year = course_form.year.data
        new_course.date_of_creation = date.today().strftime("%B %d, %Y")
        new_course.name = course_form.language.data + " - " + course_form.level.data + " - " + course_form.month.data \
                          + " - " + course_form.year.data
        db.session.add(new_course)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('course_creation.html', form=course_form, logged_in=current_user.is_authenticated,
                           user_name=user_name)


@app.route('/choose_course')
@login_required
def choose_course():
    user_name = current_user.name
    all_courses = db.session.query(Course).all()
    return render_template('choose_course.html', all_courses=all_courses, logged_in=current_user.is_authenticated,
                           user_name=user_name)


@app.route('/add_course/<course_name>')
@login_required
def add_course(course_name):
    current_user.study_course = course_name
    db.session.commit()
    return redirect(url_for('profile'))


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    course_name = ''
    user_name = current_user.name
    if current_user.id == 1:
        return redirect(url_for('admin'))
    else:
        search_form = SearchForm()
        search_list = []
        allow_to_edit = False
        if search_form.validate_on_submit():
            all_words = db.session.query(Word).all()
            if current_user.has_courses:
                allow_to_edit = True
            for word in all_words:
                if search_form.word.data.lower() in word.name.lower() or search_form.word.data.lower() in\
                        word.meaning.lower():
                    search_list.append(word)
            return render_template("search_result.html", search_list=search_list, word=search_form.word.data,
                                   allow_to_edit=allow_to_edit, logged_in=current_user.is_authenticated,
                                   user_name=user_name)
        elif current_user.has_courses:
            user_role = "course_manager"
            for course in current_user.has_courses:
                course_name = course.name
            course_to_learn = Course.query.filter_by(name=course_name).first()
            section_list = []
            for section in course_to_learn.has_section:
                section_list.append(section)
            return render_template("profile.html", logged_in=current_user.is_authenticated, user_name=user_name,
                                   user_role=user_role, course_name=course_name, section_list=section_list[::-1],
                                   searchform=search_form)
        else:
            course_to_learn = Course.query.filter_by(name=current_user.study_course).first()
            section_list = []
            for section in course_to_learn.has_section:
                section_list.append(section)
            return render_template("profile.html", logged_in=current_user.is_authenticated, user_name=user_name,
                                   section_list=section_list[::-1], searchform=search_form)

# +++++++++++++++++++++++++++++++++++++++++++++++++ Learning ++++++++++++++++++++++++++++++++++++++++++++++++++++++


word_list = []
word_name = ''
word_meaning = ''
word_description = ''
word_gender = ''
word__id = ''


@app.route('/select_word')
@login_required
def select_word():
    global word_name, word__id, word_meaning, word_gender, word_description
    word_meaning = ''
    word_gender = ''
    word_name = ''
    word__id = ''
    word_description = ''
    if word_list:
        selected_word = random.choice(word_list)
        word_name = selected_word.meaning
        word__id = selected_word.id
    else:
        word_name = "You Finished Learning This Section"
    return redirect(url_for('show_learning'))


@app.route('/show_answer')
@login_required
def show_answer():
    global word_meaning, word_gender, word_description
    selected_word = Word.query.get(word__id)
    word_gender = selected_word.gender
    word_meaning = selected_word.name
    word_description = selected_word.description
    return redirect(url_for('show_learning'))


@app.route('/pack_word_list/<int:section_id>')
@login_required
def pack_word_list(section_id):
    global word_list
    word_list = []
    section = Section.query.get(section_id)
    for word in section.has_word:
        word_list.append(word)
    return redirect(url_for('select_word'))


@app.route('/remove_from_list')
@login_required
def remove_from_list():
    global word_list
    word_to_remove = Word.query.get(word__id)
    if word_list:
        for word in word_list:
            if word.id == word_to_remove.id:
                word_list.remove(word)
    return redirect(url_for('select_word'))


@app.route('/show_learning')
@login_required
def show_learning():
    user_name = current_user.name
    return render_template("learning.html", logged_in=current_user.is_authenticated, user_name=user_name,
                           word_name=word_name, word_id=word__id, word_meaning=word_meaning, word_gender=word_gender,
                           word_description=word_description)


# +++++++++++++++++++++++++++++++++++++++++++++++++ End of Learning ++++++++++++++++++++++++++++++++++++++++++++++++


def course_manager_only(f):
    @wraps(f)
    def decorated_function2(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.has_courses:
                return f(*args, **kwargs)
        return abort(403)

    return decorated_function2


@app.route('/section_manage', methods=['POST', 'GET'])
@course_manager_only
def section_manage():
    user_name = ''
    section_list = []
    section_form = SectionForm()
    if current_user.is_authenticated:
        for course in current_user.has_courses:
            for section in course.has_section:
                section_list.append(section)
        user_name = current_user.name
        if section_form.validate_on_submit():
            new_section = Section()
            new_section.name = section_form.name.data
            for course in current_user.has_courses:
                new_section.belong_to_course_id = course.id
            db.session.add(new_section)
            db.session.commit()
            new_added_section = Section.query.filter_by(name=section_form.name.data).first()
            section_id = new_added_section.id
            return redirect(url_for('word_manage', section_id=section_id))
    return render_template("section_manage.html", user_name=user_name, logged_in=current_user.is_authenticated,
                           form=section_form, section_list=section_list[::-1])


@app.template_global('number_of_words')
def number_of_words(sec_id):
    referred_section = Section.query.get(sec_id)
    return len(referred_section.has_word)


@app.route("/delete_section/<int:section_id>")
@course_manager_only
def delete_section(section_id):
    section_to_delete = Section.query.get(section_id)
    for words in section_to_delete.has_word:
        word_to_delete = Word.query.get(words.id)
        db.session.delete(word_to_delete)
        db.session.commit()
    db.session.delete(section_to_delete)
    db.session.commit()
    return redirect(url_for('section_manage'))


@app.route('/word_manage/section/<section_id>', methods=['POST', 'GET'])
@course_manager_only
def word_manage(section_id):
    word_form = WordForm()
    user_name = ''
    section = Section.query.filter_by(id=int(section_id)).first()
    word_list2 = []
    for words in section.has_word:
        word_list2.append(words)
    section_name = section.name
    if current_user.is_authenticated:
        user_name = current_user.name
        if word_form.validate_on_submit():
            new_word = Word()
            new_word.name = word_form.name.data
            new_word.meaning = word_form.meaning.data
            if word_form.gender:
                new_word.gender = word_form.gender.data
            if word_form.description:
                new_word.description = word_form.description.data
            new_word.belong_to_section_id = section_id
            db.session.add(new_word)
            db.session.commit()
            return redirect(url_for('word_manage', section_id=section_id))
    return render_template("word_manage.html", user_name=user_name, logged_in=current_user.is_authenticated,
                           form=word_form, section_name=section_name, word_list=word_list2, section_id=section_id)


@app.route("/delete_word/<int:section_id>/<int:word_id>")
@course_manager_only
def delete_word(section_id, word_id):
    word_to_delete = Word.query.get(word_id)
    db.session.delete(word_to_delete)
    db.session.commit()
    return redirect(url_for('word_manage', section_id=section_id))


@app.route("/edit_word/<int:section_id>/<int:word_id>", methods=['POST', 'GET'])
@course_manager_only
def edit_word(section_id, word_id):
    word_to_edit = Word.query.get(word_id)
    user_name = current_user.name
    word_edit_form = EditWordForm(
        name=word_to_edit.name,
        meaning=word_to_edit.meaning,
        gender=word_to_edit.gender,
        description=word_to_edit.description
    )
    if word_edit_form.validate_on_submit():
        word_to_edit.name = word_edit_form.name.data
        word_to_edit.meaning = word_edit_form.meaning.data
        word_to_edit.gender = word_edit_form.gender.data
        word_to_edit.description = word_edit_form.description.data
        db.session.commit()
        return redirect(url_for('word_manage', section_id=section_id))
    return render_template('edit_word.html', form=word_edit_form, logged_in=current_user.is_authenticated,
                           section_id=section_id, user_name=user_name)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)


