from flask import render_template, url_for, redirect, flash, request, send_file
from portal import app, db, bcrypt
from portal.forms import RegistrationForm, LoginForm, AddUsersForm, ChangePasswordForm
from portal.forms import PostForm, TurnInForm
from portal.models import User, Post, Assignment, Reply
from flask_login import login_user, current_user, logout_user, login_required
from io import BytesIO

@app.route("/")
@app.route("/home/", methods=['GET', 'POST'])
def home():
    all_posts = Post.query.all()
    posts = []
    if current_user.is_authenticated:
        for post in reversed(all_posts):
            if post.author.school == current_user.school:
                posts.append(post)
    return render_template('home.html', posts=posts)

@app.route("/about/")
def about():
    return render_template('about.html')

@app.route("/register/", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        current_num = len(User.query.filter_by(user_type='admin').all())
        log_id = f"ad{current_num+1}"
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        admin = User(login_id=log_id,user_type='admin', email=form.email.data,
                         name=form.name.data, school=form.school.data, password=hashed_password)
        db.session.add(admin)
        db.session.commit()
        login_user(admin)
        flash(f'{form.school.data} is registered!', 'success')
        flash(f'Your login id is {admin.login_id}', 'success')
        return redirect(url_for('about'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login/", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login_id=form.login_id.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if bcrypt.check_password_hash(user.password, '123456'):
                return redirect(next_page) if next_page else redirect(url_for('change_pass'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Log in unsuccessful. Please check username or password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/addusers/", methods=['GET', 'POST'])
@login_required
def add_users():
    form=AddUsersForm()
    if current_user.user_type == 'admin':
        if form.validate_on_submit():
            current_num = len(User.query.filter_by(user_type=form.user_type.data).all())
            log_id = f"{form.user_type.data[0:2]}{current_num+1}"
            password = bcrypt.generate_password_hash('123456').decode('utf-8')
            new_user = User(login_id=log_id, user_type=form.user_type.data, name=form.name.data,
                            email=form.email.data, school=current_user.school, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash(f'{new_user.login_id} is added', 'success')
            return redirect(url_for('add_users'))
    return render_template('add_users.html', form=form, title='Account')

@app.route("/account/", methods=['GET', 'POST'])
@login_required
def account():
    return render_template('account.html')

@app.route("/changepass/", methods=['GET', 'POST'])
@login_required
def change_pass():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.current_password.data):
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            current_user.password = hashed_password
            db.session.commit()
            flash('Password changed successfully', 'success')
            return redirect(url_for('account'))
        else:
            flash('Unsuccessful. Try again', 'danger')
    return render_template('change_pass.html', form=form)

@app.route("/post/new/", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        if current_user.user_type != 'student':
            uploaded_file = request.files['file']
            file_name = uploaded_file.filename
            post = Post(title=form.title.data, content=form.content.data,
                author=current_user, doc=uploaded_file.read(), assigned_doc_name=file_name)
        else:
            post = Post(title=form.title.data, content=form.content.data,
                author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post created', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', form=form, title='New Post')

@app.route("/download/")
@login_required
def download():
    file_data = Post.query.filter_by(id=current_post.id).first()
    if file_data.doc:
        return send_file(BytesIO(file_data.doc), attachment_filename=file_data.assigned_doc_name,
                                as_attachment=True)

@app.route("/post/<int:post_id>/", methods=['GET', 'POST'])
@login_required
def post(post_id):
    global current_post
    global turn_ins
    current_post = Post.query.get_or_404(post_id)
    post_id = current_post.id
    turn_ins = Assignment.query.filter_by(post=current_post.id).all()
    turn_in_len = len(turn_ins)
    post_user_type = current_post.author.user_type
    all_replies = Reply.query.filter_by(post_id=current_post.id).all()
    replies = []
    for reply in reversed(all_replies):
        replies.append(reply)

    form = TurnInForm()
    if form.validate_on_submit():
        uploaded_file = request.files['file']
        assign_name = uploaded_file.filename
        assignment = Assignment(submitted_doc=uploaded_file.read(),
                                post=post_id, doc_name=assign_name, st_name=current_user.name)
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment turned in!', 'success')
        return redirect(url_for('home'))

    return render_template('post.html', post=current_post, replies=replies, form=form, turn_ins=turn_ins, turn_in_len=turn_in_len, post_user_type=post_user_type)

@app.route("/reply/<int:postid>/", methods=['GET', 'POST'])
def reply(postid):
    form = PostForm()
    if request.method == 'POST':
        reply = Reply(user_id=current_user.id, content=form.content.data, 
                    post_id=postid, u_name=current_user.name)
        db.session.add(reply)
        db.session.commit()
        flash('Replied to {}'.format(Post.query.filter_by(id=postid).first().author.name), 'success')
        return redirect(url_for('post', post_id=postid))
    return render_template('reply.html', form=form)

@app.route("/download_assignment/<int:i>/")
@login_required
def download_assign(i):
    return send_file(BytesIO(turn_ins[i].submitted_doc),
            attachment_filename=turn_ins[i].doc_name, as_attachment=True)

@app.route("/logout/")
def logout():
    logout_user()
    return redirect(url_for('home'))
