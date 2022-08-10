<html lang="en">
<head>
    <meta charset="utf-8" />
    <title> JavaScript - forms </title>
    <script type="text/javascript">

            function write_name() {
                var number_parra = document.getElementById('teamNumber');
                var name = document.getElementByID('name');
            
                number_parra.innerHTML = "teamNumber" + name.value;
            }

    </script>
</head>
<body>
    <p id="teamNumber"></p>
    <form>
            Team Number:<input type="text" id="name"/><br /> 
            <input type="button" value="done"/>
    </form>
</body>
</html>