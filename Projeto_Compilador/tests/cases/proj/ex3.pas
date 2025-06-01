program Fatorial;
    var
        str1: String;
        n, i, fat: Integer;
    begin
        WriteLn('Introduza um número inteiro positivo:');
        ReadLn(str1);
        n := Atoi(str1);
        fat := 1;
        for i := 1 to n do
            fat := fat * i;
        Write('Fatorial de ');
        Write(n);
        Write(': ');
        WriteLn(fat);
    end.