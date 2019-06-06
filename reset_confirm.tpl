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
       <div class="alerts">
        %for type, text in get('alerts', []):
          <div class="alert {{ type }}">{{ text }}</div>
        %end
      </div>
      <form  method="post">
          <label for="code-confirm">用户ID</label>
         <input id="user-id" name="user-id" value="{{ uid }}" type="text" disabled="disabled">

        <label for="code-confirm">邮箱验证码</label>
        <input id="code-confirm" name="code-confirm" type="password" >

        <label for="new-password">新密码</label>
        <input id="new-password" name="new-password" type="password" >

        <label for="confirm-password">确认新密码</label>
        <input id="confirm-password" name="confirm-password" type="password">

        <button type="submit">确定</button>
      </form>


    </main>
  </body>
</html>
