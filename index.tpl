<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">

    <title>{{ page_title }}</title>

    <link rel="stylesheet" href="{{ url('static', filename='style.css') }}">
  </head>

  <body>
    <main>
      <h2>{{ page_title }}</h2>

      <form method="post">

        <label for="username">用户名(姓名拼音)</label>
        <input id="username" name="username" value="{{ get('username', '') }}" type="text" required autofocus>

        <label for="old-password">旧密码(新用户为初始密码)</label>
        <input id="old-password" name="old-password" type="password" required>

        <label for="new-password">新密码</label>
        <input id="new-password" name="new-password" type="password"
            pattern=".{8,}" oninvalid="SetCustomValidity('Password must be at least 8 characters long.')" required>

        <label for="confirm-password">确认新密码</label>
        <input id="confirm-password" name="confirm-password" type="password"
            pattern=".{8,}" oninvalid="SetCustomValidity('Password must be at least 8 characters long.')" required>

        <button type="submit">确定</button>
        <a class='slot_pass' href="/reset.html">忘记密码？</a>
      </form>

      <div class="alerts">
        %for type, text in get('alerts', []):
          <div class="alert {{ type }}">{{ text }}</div>
        %end
      </div>
    </main>
  </body>
</html>
