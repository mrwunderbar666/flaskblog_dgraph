from flask import (Blueprint, render_template, url_for, flash, redirect, request, abort)
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog import dgraph
from flaskblog.models import User
from flaskblog.users.forms import (RegistrationForm, LoginForm,
                             UpdateProfileForm, RequestResetForm, ResetPasswordForm)
from flaskblog.users.utils import save_picture, send_reset_email

users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = {'username': form.username.data,
                    'email': form.email.data,
                    'pw': form.password.data}
        new_uid = dgraph.create_user(new_user)

        flash(f'Accounted created for {new_uid}!', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        if user and dgraph.user_login(form.email.data, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'You have been logged in', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash(f'Login unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route('/logout')
def logout():
    logout_user()
    flash(f'You have been logged out', 'info')
    return redirect(url_for('main.home'))


@users.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.avatar_img.data:
            form.avatar_img.data.filename = save_picture(form.avatar_img.data)
        current_user.update_profile(form)
        flash(f'Your account has been updated', 'success')
        return redirect(url_for('users.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        # form.avatar_img.data = current_user.avatar_img
    image_file = url_for(
        'static', filename='profile_pics/' + current_user.avatar_img)
    return render_template('profile.html', title='Profile', profile_pic=image_file, form=form)


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_password = {'pw': form.password.data}
        new_uid = dgraph.update_entry(user.id, new_password)

        flash(f'Password updated for {user.id}!', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
