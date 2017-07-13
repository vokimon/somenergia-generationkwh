<%

    import datetime


    receiptDate = datetime.datetime.today().strftime("%d-%m-%Y")

    ownerName = "Pepito Pepitez Perez"
    ownerNif = "12345678-Z"

    inversionId = "GKWH001"
    inversionInitialAmount = "1.000,00"
    inversionPurchaseDate = "20-05-2015"
    inversionExpirationDate = "19-05-2040"
    inversionPendingCapital = "960,00"
    inversionBankAccount = "ES25 0081 5273 6200 0103 9910"

    amortizationName = "GKWH0000001-AMOR2017"
    amortizationAmount = "40,00"
    amortizationDate = "20-05-2017"
    amortizationNumPayment = "1"
    amortizationTotalPayments = "24"
%>
<html>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<head>
    <title> Liquidació préstec Generation kWh </title>
    <style type="text/css">
    ${css}
    img {
        width: 120px;
        height: 120px;
        margin-left: 10px;
    }
    .logos {
        float: left;
    }
    table a:link {
        color: #666;
        font-weight: bold;
        text-decoration:none;
    }
    table {
        font-family:Arial, Helvetica, sans-serif;
        color:#666;
        font-size:12px;
        text-shadow: 1px 1px 0px #fff;
        background:#e0e0e0;
        margin-left:auto;
        margin-right:auto;
        width: 60%;
        border:#ccc 1px solid;

        -moz-border-radius:3px;
        -webkit-border-radius:3px;
        border-radius:3px;

        -moz-box-shadow: 0 1px 2px #d1d1d1;
        -webkit-box-shadow: 0 1px 2px #d1d1d1;
        box-shadow: 0 1px 2px #d1d1d1;
    }
    table th {
        padding:10px 25px;
        border-top:1px solid #fafafa;
        border-bottom:1px solid #e0e0e0;

        background: #ededed;
        background: -webkit-gradient(linear, left top, left bottom, from(#ededed), to(#ebebeb));
        background: -moz-linear-gradient(top,  #ededed,  #ebebeb);
    }
    table th:first-child {
        text-align: center;
        padding-left:20px;
    }
    table tr:first-child th:first-child {
        -moz-border-radius-topleft:3px;
        -webkit-border-top-left-radius:3px;
        border-top-left-radius:3px;
    }
    table tr:first-child th:last-child {
        -moz-border-radius-topright:3px;
        -webkit-border-top-right-radius:3px;
        border-top-right-radius:3px;
    }
    table tr:last-child td:first-child {
        -moz-border-radius-bottomleft:3px;
        -webkit-border-bottom-left-radius:3px;
        border-bottom-left-radius:3px;
    }
    table tr:last-child td:last-child {
        -moz-border-radius-bottomright:3px;
        -webkit-border-bottom-right-radius:3px;
        border-bottom-right-radius:3px;
    }
    table tr {
        text-align: left;
        padding-left:20px;
    }
    table td:first-child {
        padding-left:20px;
        border-left: 0;
    }
    table td {
        padding:5px 18px;
        border-top: 1px solid #ffffff;
        border-bottom:1px solid #e0e0e0;
        border-left: 1px solid #e0e0e0;

        background: #fafafa;
        background: -webkit-gradient(linear, left top, left bottom, from(#fbfbfb), to(#fafafa));
        background: -moz-linear-gradient(top,  #fbfbfb,  #fafafa);
    }
    table tr:last-child td {
        border-bottom:0;
    }
    #account{
        text-align: center;
    }
    #cabecera{
        float: right;
        padding-top: 20px;
    }

    </style>
</head>
<body>

    <div class="logos">
        <img src="${addons_path}/som_generationkwh/report/Logo-SomEnergia-blanco-quadrado-250x250px.jpg" />
        <img src="${addons_path}/som_generationkwh/report/Logo_Generation-04-Horizontal.jpg" />
        <p id="cabecera">Liquidació Generation kWh ${receiptDate} </ p>
    </ div>
    <div>
    <table>
        <tr>
            <th colspan="2"><b>Dades Préstec Generation kWh: ${inversionId}</b></th>
        </tr>
        <tr>
            <td colspan="2"> Titular: ${ownerName}</td>

        </tr>
        <tr>
            <td> NIF:  ${ownerNif} </td>
            <td> Import Inicial:  ${inversionInitialAmount} € </td>
        </tr>
        <tr>
            <td> Data formalització: ${inversionPurchaseDate}</td>
            <td> Data venciment: ${inversionExpirationDate}</td>
        </tr>
    </table>
    </br>
    <table>
        <tr>
            <th colspan="2"><b>Amortització Actual: ${amortizationName} </b> </th>
        </tr>
        <tr>
            <td> Import: ${amortizationAmount} € </td>
            <td> Data: ${amortizationDate} </td>
        </tr>
        <tr>
            <td> Pagament nº:  ${amortizationNumPayment} de ${amortizationTotalPayments} </td>
            <td> Pendent de retornar: ${inversionPendingCapital} € </td>
        </tr>
    </table>
    </br>
    <table>
        <tr>
            <th colspan="2"><b> Compte on es realizarà l'ingrés </b></th>
        </tr>
        <tr>
            <td id="account"> ${inversionBankAccount} </td>
        </tr>
    </table>
    </div>
</body>
</html>
