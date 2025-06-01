program NumeroPrimo;
    var
        str1: String;
        num, i: Integer;
        primo: Boolean;
    begin
        WriteLn('Introduza um número inteiro positivo:');
        ReadLn(str1);
        num := Atoi(str1);
        primo := true;
        i := 2;
        while (i <= (num div 2)) and primo do
            begin
                if (num mod i) = 0 then
                    primo := false;
                i := i + 1;
            end;
        if primo then begin
            Write(num);
            WriteLn(' é um número primo')
        end else begin
            Write(num);
            WriteLn(' não é um número primo')
        end
    end.