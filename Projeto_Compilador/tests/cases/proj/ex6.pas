program BinarioParaInteiro;
    var
        bin: string;
        i, valor, potencia: integer;
    begin
        WriteLn('Introduza uma string binária:');
        ReadLn(bin);

        valor := 0;
        potencia := 1;
        for i := Length(bin) downto 1 do
            begin
                if bin[i] = '1' then
                    valor := valor + potencia;
                potencia := potencia * 2;
            end;
            
        WriteLn('O valor inteiro correspondente é: ', valor);
    end.