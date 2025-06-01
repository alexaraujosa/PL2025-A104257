program TemperatureConversion(Output);
    { Program 3.1 - Example program illustrating constant
    and type definition and variable declaration parts. }

    const
        Bias = 32; Factor = 1.8; Low = -20; High = 39;
        Separator = '  ---'; Blanks = '   '
    type
        CelciusRange = Low..High
            { a subrange type-see Chapter 5 }; 
    var
        Degree: CelciusRange;
begin
    for Degree := Low to High do
        begin
            Write(Output, Degree, ' C' , Separator);
            Write(Output, Round(Degree*Factor + Bias), ' F');
            if odd(Degree) then Writeln(Output)
            else Write(Output, Blanks)
        end;
    Writeln(Output)
end .