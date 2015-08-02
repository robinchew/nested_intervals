-- sqlite3 db.sqlite < create.sql

drop table matrix;
create table matrix(
    name char,
    a11 integer,
    a12 integer,
    a21 integer,
    a22 integer,
    foreign key (a12, a22) references matrix (a11, a21)
);
create unique index uniqueness ON matrix(a11, a21);

/*
insert into matrix values('House 1',   1, -1, 2, -1);
insert into matrix values('Room 1.1',  1, -1, 3, -2);
insert into matrix values('Room 1.2',  2, -1, 5, -2);
insert into matrix values('Room 1.3',  3, -1, 7, -2);
insert into matrix values('House 2',   2, -1, 3, -1);
insert into matrix values('Room 2.1',  3, -2, 5, -3);
*/

--insert into matrix values('Root 0',   1, -1, 1 ,0 );
insert into matrix values('House 1',   1, 1, 2, 1);
insert into matrix values('Room 1.1',  1, 1, 3, 2);
insert into matrix values('Room 1.2',  2, 1, 5, 2);
insert into matrix values('Room 1.2.1',3, 2, 8, 5);
insert into matrix values('Room 1.3',  3, 1, 7, 2);
insert into matrix values('House 2',   2, 1, 3, 1);
insert into matrix values('Room 2.1',  3, 2, 5, 3);

select 'children', child.name from matrix parent, matrix child
where parent.name = 'House 1'
and parent.a11 = child.a12 and parent.a21 = child.a22 ;


/*
select 'descendants', descendant.* from matrix descendant, matrix node
where node.a11 * descendant.a21 >= node.a21 * descendant.a11
and   node.a11 * descendant.a22 >= node.a21 * descendant.a12
and node.name = 'House 2';
*/

select 'descendant', descendant.* from matrix descendant, matrix node
where descendant.a11*node.a21 < descendant.a21*node.a11
and descendant.a11*(node.a21-node.a22) > descendant.a21*(node.a11-node.a12)
and node.name = 'House 1';

select 'descendant2', descendant.* from matrix descendant, matrix node
where descendant.a11*node.a21 < descendant.a21*node.a11
and descendant.a11*(node.a21-node.a22) > descendant.a21*(node.a11-node.a12)
and node.name = 'House 2';

select 'descendant 1-2', descendant.* from matrix descendant, matrix node
where descendant.a11*node.a21 < descendant.a21*node.a11
and descendant.a11*(node.a21-node.a22) > descendant.a21*(node.a11-node.a12)
and node.name = 'Room 1.2';

select 'descendant 1-2-1', descendant.* from matrix descendant, matrix node
where descendant.a11*node.a21 < descendant.a21*node.a11
and descendant.a11*(node.a21-node.a22) > descendant.a21*(node.a11-node.a12)
and node.name = 'Room 1.2.1';

select 'descendant 1-3', descendant.* from matrix descendant, matrix node
where descendant.a11*node.a21 < descendant.a21*node.a11
and descendant.a11*(node.a21-node.a22) > descendant.a21*(node.a11-node.a12)
and node.name = 'Room 1.3';

/*
select B.* from matrix A, matrix B
where B.a21*A.a12 - B.a11*A.a22 > -B.a11*A.a21 + B.a21*A.a11
and B.a12*A.a22 - B.a22*A.a12 > -B.a22*A.a11 + B.a12*A.a21
and A.name = 'House 1';
*/
