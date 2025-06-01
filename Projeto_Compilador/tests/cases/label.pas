procedure B; { block B }
    label 3, 5;
begin
    goto 3;
3: Writeln('Hello');
5: if P then
    begin S; goto 5 end; { while P do S }
    goto 1; { this causes early termination of
    the activation of B }
    Writeln('Goodbye')
end; { block B } 