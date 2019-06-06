<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">

    <title>重置密码</title>

    <link rel="stylesheet" href="{{ url('static', filename='style.css') }}">
  </head>

  <body>
    <main>
      <div>
      <h2>重置密码</h2>
      <form method="post">
       <p><h5 style="color:red">重置密码会向您的工作邮箱发送一封邮件，请注意查收邮件验证码！</h5></p>
        <label for="username">用户名(姓名拼音)</label>
        <input id="username" name="username"  type="text" required autofocus>
        <button type="submit">确定</button>
      </form>
       </div>
             <div class="alerts">
        %for type, text in get('alerts', []):
          <div class="alert {{ type }}">{{ text }}</div>
        %end
      </div>
    </main>
  </body>
</html>
