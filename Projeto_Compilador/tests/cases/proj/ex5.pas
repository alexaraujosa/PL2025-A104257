program SomaArray;
    var
        str: String;
        numeros: array[1..5] of Integer;
        i, soma: Integer;
    begin
        soma := 0;
        WriteLn('Introduza 5 números inteiros:');
        for i := 1 to 5 do
            begin
                ReadLn(str);
                numeros[i] := Atoi(str);
                soma := soma + numeros[i];
            end;
            
        Write('A soma dos números é: '); 
        WriteLn(soma);
    end.