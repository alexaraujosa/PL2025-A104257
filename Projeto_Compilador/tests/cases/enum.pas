program DayTime(Output);
    { Program 5.1 - Illustrate enumerated types. }
    type 
        Days = (Mon, Tue, Wed, Thu, Fri, Sat, Sun);
        When = (Past, Present, Future);
    var
        Day: Days;
        Yesterday, Today, Tomorrow: Days;
        Time: When;
begin
    Today := Sun { Pascal can't read a value of an
    Time := Present; emumerated type from Input. };
    repeat
        case Time of
            Present: begin {Calculate Yesterday}
                Time := Past;
                if Today = Mon then Yesterday := Sun
                else Yesterday := pred(Today);
                Day := Yesterday; Write (Output, 'Yesterday');
            end;
            Past: begin {Calculate Tomorrow}
                Time := Future;
                if Today = Sun then Tomorrow := Mon
                else Tomorrow := succ(Today);
                Day := Tomorrow; Write (Output, 'Tomorrow');
            end;
            Future: begin {Reset to Present}
                Time := Present;
                Day := Today; Write (Output, 'Today');
            end;
        end;
        case Day of
            Mon: Write (Output,'Monday');
            Tue: Write (Output,'Tuesday');
            Wed: Write (Output, 'Wednesday');
            Thu: Write (Output, 'Thursday');
            Fri: Write (Output, 'Friday');
            Sat: Write (Output, 'Saturday');
            Sun: Write (Output, 'Sunday');
        end;
        Writeln(Output, Ord(Time) - 1)
    until Time = Present
end .