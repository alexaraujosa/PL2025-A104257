program BinarioParaInteiro;
    var
        bin: String;
        valor: Integer;
    function BinToInt(bin: String): Integer;
        var
            i, valor, potencia: Integer;
        begin
            valor := 0;
            potencia := 1;

            for i := Length(bin) downto 1 do
                begin
                    if bin[i] = '1' then
                        valor := valor + potencia;
                    potencia := potencia * 2;
                end;

            BinToInt := valor;
        end;
    begin
        WriteLn('Introduza uma string binária:');
        ReadLn(bin);

        valor := BinToInt(bin);
        Write('O valor inteiro correspondente é: ');
        WriteLn(valor);
    end.