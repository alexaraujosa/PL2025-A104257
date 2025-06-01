program HelloWorld(correct   , externals,    list);
    label 123, 100, 99, 1, 456;
    const
        Avogadro = 6.02e23;
        PageLength = 60;
        Border = '# * ';
        MyMove = True;
        N = 10;
        Size = 15;
        Stringlength = 255;
    type
        { Simple Types }
        { - Ordinal Types }
        { -- Enumerated Types }
        et1 = (Red, Orange, Yellow, Green, Blue);
        et2 = (Club, Diamond, Heart, Spade);
        et3 = (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday);

        { -- Subrange Types }
        st1 = 1..N;
        st2 = -10 .. +10;
        st3 = Monday .. Friday;

        { - Structural Types }
        { -- Array Types }
        at1 = array [1..100] of Real;
        at2 = array [1 .. 10, 1 .. 20] of Integer;
        at3 = array [Boolean] of Color;
        at4 = array [Size] of packed array ['a' .. 'z'] of Boolean;
        at5 = packed array [1.. Stringlength] of Char;
        at6 = packed array [1 .. 2] of Var;

        { -- Record Types }
        { --- Fixed Record Types }
        frt1 = record Re, Im: Real end; 
        frt2 = packed record
            Year: 1900 .. 2100;
            Mo: (Jan, Feb, Mar, Apr, May, Jun,
                    Jul, Aug, Sep, Oct, Nov, Dec);
            Day: 1 .. 31
        end;
        frt3 = record
            Kind: (Ball, Top, Boat, Doll, Blocks,
            Game, Model, Book);
            Cost: Real;
            Received: Date;
            Enjoyed: (Alot, Some, Alittle, None);
            Broken, Lost: Boolean
        end;

        { --- Variant Record Types }
        vtra1 = (A,B,C);
        vrt1 = record
            case PM: vtra1 of
                A : (
                    FieldA1: 1 .. 10;
                    FieldA2: (FA2a, FA2b, FA2c)
                );
                B, C: (
                    FieldB1: 20 .. 30;
                    FieldB2: (FB2a, FB2b)
                )
        end;
        vrt2 = record
            Name: record First, Last: String15 end;
            Height: Natural { centimeters };
            Sex: (Male ,Female) ;
            Birth: Date;
            Depdts: Natural;
            case MS: Status of
                Married, Widowed: (MDate: Date);
                Divorced: (MDDate: Date; 
                            FirstD: Boolean);
                Single: ()
        end;

        { -- Set Types }
        sett1 = set of et1;
        sett2 = set of (A,B,C);

        { - Pointer Types }
        pt1 = @Test;
        pt2 = ↑Test;
        pt3 = pt1;


        T = et1;
        T2 = st2;
        U = at1;
    var
        v1, v2: (Yes, No, Yesnt, Nont);
        v3: 1..10;
        v4: array [1..100] of Real;
        { v5: record Re, Im: Real end; } { Will cause a conflict with record frt1 and I can't be fucked to change the Symbol Table }
        v5: record Re, Im: Real end;
        v6: set of v1;
        v7: @v6;
        v8: pt1;

        
    procedure P1; Forward;
    procedure P2(X: T); Forward;
    procedure P3(Y: T); Forward;
    procedure P4(var PV: pt1); Forward;
    procedure P5(var F: at5; var X: Integer);
        const test = 123;
        begin
        
        end;
    procedure P6(procedure PH(A2: T)); Forward;
    function F1(FA1: T; FA2: T2): R; Forward;
    function F2(function FA1(FAA2: U): RA; FA2: T2): R; Forward;
    begin
        { Simple Statements }
        { - Assignment Statements }
        1: x := Y + GrayScale[31];
        P := (1 <= I) and (I < idk);
        I := sqr(K) - (I*J);
        Hue2 := [Blue, succ(C)];

        { - Procedure Statements }
        Next;
        Transpose(A,N,N);
        Bisect (Fct, -1.0, +1.0, X);
        Writeln(Output, ' Title');

        { - Goto Statements }
        456: goto 123;
        goto 456;

        { Structured Statements }
        { - Compound Statements }
        begin end;
        begin W := X; X := Y; Y := W end;

        { - Conditional Statements }
        { -- If Statements }
        if e1 then if e2 then sl else s2;
        if e1 then
            begin if e2 then sl else s2 end;
        if x < 1.5 then W := X + Y else W := 1.5;
        if P1 <> nil then PI := P1↑;

        { -- Case Statements }
        case Operator of
            Plus: W:= X + Y;
            Minus: W:= X - Y;
            Times: W:= X * Y
        end;
        case I of
            1 : Y := sin (X) ;
            2 : Y := cos (X) ;
            3 : Y := exp (X) ;
            4 : Y := In(X)
        end;
        case P1@.Status of
            Married, Coupled: P2 := P1@.SignificantOther;
            Single: P2:= nil;
        end;

        { - Repetitive Statements }
        { -- While Statements }
        while B do S;
        while GrayScale[1] < 0 do I := succ(1);
        while I > 0 do
            begin
                if odd (I) then Y:= Y * X;
                I := I div 2;
                X := sqr(X)
            end;
        while not eof(F) do begin
            p(F@); Get(F)
        end;

        { -- Repeat Statements }
        repeat S until B;
        repeat K := I mod J; I := J; J := K; until J = 0;
        repeat
            P (F@);
            Get(F)
        until eof (F);

        { -- For Statements }
        for v := el to e2 do s;
        for I := 1 to 63 do
            if GrayScale[I] > 0.5 then write ('*')
            else write (' ');
        for I := 1 to n do
            for J := 1 to n do
                begin 
                    X := 0;
                    for K := 1 to n do
                        X := X + A[I,K] * B[K,J];
                    C[I,J] := X
                end;
        for Light := Red to pred(Light) do
            if Light in Hue2 then Q(Light); 

        { - With Statements }
        123: with r1, r2, rn do S;
        with r1 do
            with r1 do
                with rn do S;

        with Date do
            if Month = 12 then
                begin Month := 1; Year := succ(Year) end
            else Month := succ(Month);

        Test(test@, abc[123]);
    end
.