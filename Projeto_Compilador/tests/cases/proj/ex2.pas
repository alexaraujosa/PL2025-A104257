program Maior3;
    var
        str1, str2, str3: String;
        num1, num2, num3, maior: Integer;
    begin
        { Ler 3 números }
        WriteLn('Introduza o primeiro número: ');
        ReadLn(str1);
        num1 := Atoi(str1);

        WriteLn('Introduza o segundo número: ');
        ReadLn(str2);
        num2 := Atoi(str2);

        WriteLn('Introduza o terceiro número: ');
        ReadLn(str3);
        num3 := Atoi(str3);

        { Calcular o maior }
        if num1 > num2 then
            if num1 > num3 then maior := num1
            else maior := num3
        else
            if num2 > num3 then maior := num2
            else maior := num3;
            
        { Escrever o resultado }
        Write('O maior é: ');
        WriteLn(maior)
    end.