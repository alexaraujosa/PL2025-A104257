program HelloWorld(correct   , externals,    list);
    const
        Avogadro = 6.02e23;
        PageLength = 60;
        Border = '# * ';
        MyMove = True;
    type
        { Simple Types }
        { - Structural Types }
        { -- Array Types }
        at1 = array [1 .. 100] of Real;
        at2 = array [1 .. 10, 1 .. 20] of Integer;
        at3 = array [Boolean] of Color;
        at4 = array [Size] of packed array ['a' .. 'z'] of Boolean;

        { -- Record Types }
        { --- Fixed Record Types }
        frt1 = record Re, Im: Real end; 
        frt2 = packed record
            Year: 1900 .. 2100
            Mo: (Jan, Feb, Mar, Apr, May, Jun,
                    Jul, Aug, Sep, Oct, Nov, Dec);
            Day: 1 .. 31
        end;
.