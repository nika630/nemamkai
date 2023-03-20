import os

from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime as dt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user


app = Flask(__name__)
app.config.from_object('config')
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

# организация хранения данных в БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Профиль пользователя
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    usr_recipe = Posts.query.filter_by(creator=current_user.login)
    return render_template('account.html', usr_recipe=usr_recipe)


# Информация о пользователях
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(20), nullable=False, unique=True)
    usr_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    date = db.Column(db.DateTime, default=dt.utcnow)
    password_hash = db.Column(db.String(100))

    @property
    def password(self):
        raise AttributeError('ошибка при создании пароля')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def varify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Name %r>' % self.name


# Форма регистрации пользователя
class RegForm(FlaskForm):
    name = StringField("Введите имя", validators=[DataRequired()])
    login = StringField("Введите логин", validators=[DataRequired()])
    email = StringField("Введите электронную почту", validators=[DataRequired()])
    password_hash = PasswordField('Введите пароль', validators=[DataRequired(), EqualTo('password_hash2',
                                                                                        message='Пароли должны совпадать')])
    password_hash2 = PasswordField('Введите пароль еще раз', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


# Форма авторизации пользователя
class LoginForm(FlaskForm):
    login = StringField("Введите электронную почту", validators=[DataRequired()])
    password_hash = PasswordField("Введите пароль", validators=[DataRequired()])
    submit = SubmitField('Войти')


# Создание поста
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    food = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=dt.utcnow)
    creator = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Article %r>' % self.id


# Форма поиска рецептов
class SearchForm(FlaskForm):
    searched = StringField("Поиск рецепта", validators=[DataRequired()])
    submit = SubmitField('Поиск')


@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html")


# Информация о сайте
@app.route('/about')
def about():
    return render_template("about.html")


# Все статьи
@app.route('/all_posts')
def posts():
    return render_template("all_posts.html")


@app.route('/all_posts/<int:id>')
def post(id):
    return render_template(f"post{id}.html")


# Авторизация пользователя
@app.route('/user/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        usr = Users.query.filter_by(login=form.login.data).first()
        if usr:
            if check_password_hash(usr.password_hash, form.password_hash.data):
                login_user(usr)
                flash('Вход успешен')
                return redirect(url_for('account'))
            else:
                flash('Неверный пароль! Попробуйте еще раз')
        else:
            flash('Пользователь не найден')

    return render_template("login.html", form=form)


# Выход пользователя из системы
@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('login'))


# Регистрация нового пользователя
@app.route('/user/user_reg', methods=['POST', 'GET'])
def user():
    name = None
    form = RegForm()
    if form.validate_on_submit():
        usr = Users.query.filter_by(email=form.email.data).first()
        if usr is None:
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            usr = Users(usr_name=form.name.data, login=form.login.data, email=form.email.data, password_hash=hashed_pw)
            db.session.add(usr)
            db.session.commit()
        name = form.name.data
        print(form.name.data)
        form.name.data = ''
        form.login.data = ''
        form.email.data = ''
        form.password_hash.data = ''
        flash("Форма отправлена успешно")
    all_users = Users.query.order_by(Users.date)
    return render_template("user_reg.html", form=form, name=name, all_users=all_users)


# Страница рецептов добавленных пользователями
@app.route('/user_recipe')
def user_recipe():
    recipes = Posts.query.order_by(Posts.date.desc()).all()
    return render_template("user_recipe.html", recipes=recipes)


# Просмотреть рецепт полностью
@app.route('/user_recipe/<int:id>')
def view_recipe(id):
    recipe = Posts.query.get(id)
    return render_template("view_recipe.html", recipe=recipe)


# Создание нового рецепта
@app.route('/user_recipe/new_recipe', methods=['POST', 'GET'])
@login_required
def new_recipe():
    if request.method == 'POST':
        title = request.form['title']
        food = request.form['food']
        text = request.form['text']
        creator = current_user.login
        recipe = Posts(title=title, food=food, text=text, creator=creator)

        try:
            db.session.add(recipe)
            db.session.commit()
            return redirect('/user_recipe')
        except:
            return "Ошибка добавления статьи"

    else:
        return render_template("new_recipe.html")


# Удаление рецепта
@app.route('/user_recipe/<int:id>/delete')
@login_required
def delete_recipe(id):
    recipe = Posts.query.get_or_404(id)
    try:
        db.session.delete(recipe)
        db.session.commit()
        return redirect('/user_recipe')
    except:
        return "Ошибка удаления статьи"


# редактирование рецепта
@app.route('/user_recipe/<int:id>/update', methods=['POST', 'GET'])
@login_required
def update_recipe(id):
    recipe = Posts.query.get(id)
    if request.method == 'POST':
        recipe.title = request.form['title']
        recipe.food = request.form['food']
        recipe.text = request.form['text']

        try:
            db.session.commit()
            return redirect('/user_recipe')
        except:
            return "Ошибка добавления статьи"
    else:

        return render_template("update_post.html", recipe=recipe)


# Поиск по сайту
@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    recipes = Posts.query
    if form.validate_on_submit():
        post.searched = form.searched.data
        recipes = recipes.filter(Posts.title.like('%' + post.searched + '%'))
        recipes = recipes.order_by(Posts.title).all()
        return render_template("search.html", form=form, searched=post.searched, recipes=recipes)


# Передача данных в навигационную панель
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


# Страницы ошибок
# Не могу найти страницу
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# Внутренняя ошибка сервера
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
